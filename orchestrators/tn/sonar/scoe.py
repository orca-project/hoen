#!/usr/bin/env python3


# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
# Import the System and Name methods from the OS module
from os import system, name

import signal

from uuid import uuid4
import ipaddress
import time

from sonar.log import get_log
from sonar.nem import nem

from services.ndb import ndb
from services.path_engine import PathEngine

logger = get_log('sonar-scoe')

class scoe(Thread):

    def __init__(self, orch, host, port):
        Thread.__init__(self)
        self.orch = orch
        self.src_seq = ipaddress.ip_address("10.10.0.0")
        self.shutdown_flag = Event()
        self._server_bind(host, port)
        catalog = ndb()
        #agent = catalog.add_local_agent('sonar-req02', '10.0.0.30', 'ith0', 's01', 5)
        #agent = catalog.add_local_agent('sonar-p01', '10.1.0.1', 'ith0', 's05', 3)
        agent = catalog.add_local_agent('sonar-local-agent01', '100.1.3.3', 'sth01', 's01', 1)
        agent = catalog.add_local_agent('sonar-local-agent02', '100.1.3.4', 'sth01', 's05', 4)

    # Bind server to socket
    def _server_bind(self, host, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://" + host + ":" + str(port))
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

    def run(self):
        print('- Started SONAr - Self-Collector Entity')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

            try:
                # Wait for request
                request = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # Received a command
            else:
                # Start time counter
                st = time.time()
                # Service request, new service
                resp = {}
                t_id = request.get('t_id')
                # print('scoe received: ', request)
                if request.get('type') == 'config_req':
                    resp = self.get_configuration(request)
                elif request.get('type') == 'report_req':
                    resp = self.report(request)
                else:
                    resp = {
                                "id": t_id,
                                "type": "report_resp",
                                "result_code": 1
                            }
                # print('scoe resp: ', resp)
                self.send_msg(resp)

        # Terminate zmq
        self.socket.close()
        self.context.term()

    def report(self, request):
        t_id = request.get('t_id')
        catalog = ndb()
        broker = nem()
        for metric in request.get('metrics'):
            if metric.get('type') == 'latency':
                path_string = catalog.get_virtual_iface(metric.get('src') + '-' + metric.get('dst'))
                catalog.set_path_latency(path_string, metric.get('params'))
                broker.insert_metric(metric)
                #self.check_paths(path_string, metric.get('params'))
        resp = {
                    "id": t_id,
                    "type": "report_resp",
                    "result_code": 0
                }
        return resp

    '''
    def check_paths(self, path_string, metric):
        catalog = ndb()
        routes = catalog.get_routes()
        # change this format of retrieving the latency...
        latency = metric.get('max')
        affected_slices = [i for i in routes if string_path == routes[i].get('path_string') and routes[i].get('latency') is not None and routes[i].get('latency') <= latency]
    '''

    def get_configuration(self, request):
        catalog = ndb()
        agents = catalog.get_local_agents()
        t_id = request.get('t_id')
        name = request.get('name')
        if name not in agents:
            return self.error_resp(t_id, 1)

        configured_agent = self.configure_metric_paths(request)

        if configured_agent is not None:
            resp = {
                    "t_id": t_id,
                    "type": "config_resp",
                    "src": configured_agent.get('src'),
                    "dst": configured_agent.get('dst'),
                    "management_iface": agents[name].get('management_iface'),
                    "result_code": 0
                }
        else:
            resp = self.error_resp(t_id, 2)
        return resp

    def configure_metric_paths(self, request):
        catalog = ndb()
        src_agent = catalog.get_local_agent(request.get('name'))
        configured_agents = catalog.get_configured_agents()
        configured_agent = None
        if src_agent.get('name') not in configured_agents:
            dst = []
            agents = catalog.get_local_agents()
            for dst_agent_name in agents:
                if src_agent.get('name') != dst_agent_name:
                    src = self.configure_flow_rules(src_agent, agents[dst_agent_name])
                    if src is None:
                        return None
                    dst.append(agents[dst_agent_name].get('host'))
            configured_agent = catalog.add_configured_agent(src_agent, src, dst)
        return configured_agent

    def configure_flow_rules(self, src_agent, dst_agent):
        engine = PathEngine()
        catalog = ndb()
        topology = self.get_topology()
        paths = engine.get_paths(topology, src_agent.get('switch'), dst_agent.get('switch'))
        src = []
        for path in paths:
            self.src_seq = self.src_seq + 1
            src_host = str(self.src_seq)
            src.append(src_host)
            switches = engine.generate_match_switches(topology, path, src_agent.get('port'), dst_agent.get('port'))
            route = {
                'ipv4_src': src_host,
                'ipv4_src_netmask': '255.255.255.255',
                'ipv4_dst': dst_agent.get('host'),
                'ipv4_dst_netmask': '255.255.255.255',
                'min_rate': None,
                'max_rate': None,
                'priority': 10,
                'switches': switches
                }
            s_id = str(uuid4())
            success, msg = self.orch.ovs_ctl.create_slice(
                **{'s_id': s_id,
                    'route': route
                    })
            if not success:
                return None
            addresses = src_host + '-' + dst_agent.get('host')
            path_string = '-'.join(map(str, path))
            catalog.add_virtual_iface(addresses, path_string)
        return src

    def get_topology(self):
        (topo_success, topo_msg) = self.orch.ovs_ctl.get_topology()    
        if not topo_success:
            return None

        topology = topo_msg.get('topology')
        catalog = ndb()
        catalog.set_topology(topology)
        return topology

    def error_resp(self, t_id, code):
        return {
                    "t_id": t_id,
                    "type": "config_resp",
                    "result_code": code
                }

    def send_msg(self, message):
        # Send a message with a header
        self.socket.send_json(message)