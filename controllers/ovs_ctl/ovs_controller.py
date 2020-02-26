#!/usr/local/bin/ryu-manager
# Hack to load parent module
from sys import path

# Import the Template Controller
from base_controller import base_controller
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal

import argparse

import time

from ryu.lib import hub
hub.patch()

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp 
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types

from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_4
from ryu.ofproto import ofproto_v1_5

from ryu.exception import RyuException
from ryu.lib import ofctl_v1_0
from ryu.lib import ofctl_v1_2
from ryu.lib import ofctl_v1_3
from ryu.lib import ofctl_v1_4
from ryu.lib import ofctl_v1_5
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import WSGIApplication

from collections import defaultdict
from sonar.nsb import nsb

supported_ofctl = {
    ofproto_v1_0.OFP_VERSION: ofctl_v1_0,
    ofproto_v1_2.OFP_VERSION: ofctl_v1_2,
    ofproto_v1_3.OFP_VERSION: ofctl_v1_3,
    ofproto_v1_4.OFP_VERSION: ofctl_v1_4,
    ofproto_v1_5.OFP_VERSION: ofctl_v1_5,
}

def cls():
    system('cls' if name == 'nt' else 'clear')

class ovs_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting OVS Controller')

        self.ovs = kwargs.get('ovs')

        cls()

        # Hold information about the slices
        self.slice_list = {} 

    def pre_exit(self):
     # Terminate the OVS SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def get_topology(self, **kwargs):
        return True, {'topology': self.ovs.topology}

    def create_slice(self, **kwargs):
        single = time.time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        route = kwargs.get('route', None)
        print('create s_id ', s_id, 'route ', route)

        # Check for validity of the slice ID

        if s_id in self.slice_list:
            print('updating slice ', s_id)
        #    return False, 'Slice ID already exists'
        # Check for validity of the route
        if not route:
            print('did not work, took',  + (time.time() - single)*1000, 'ms')
            return False, 'Missing route'

        # Add the slice to the slice list
        self.slice_list[s_id] = {
                'route': route }

        # Iterate over the list of switches
        for switch in route['switches']:
            # Get the datapath
            datapath = self.ovs.switches[switch['node']]
            # Extract the datapath parameters
            dpid = datapath.id
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            queue = self.define_queue(route, datapath)

            # ip_src, ip_dst, s, p_in, p_out)
            # Creating ingress match and actions which will be send to ovs-switch
            match = parser.OFPMatch(
                    eth_type=switch['eth_type'],
                    in_port=(switch['in_port']),
                    ipv4_src=(route['ipv4_src'], route['ipv4_src_netmask']),
                    ipv4_dst=(route['ipv4_dst'], route['ipv4_dst_netmask'])
                )
            #actions = [parser.OFPActionOutput(switch['out_port'])]
            actions = [parser.OFPActionSetQueue(queue), parser.OFPActionOutput(switch['out_port'])]

            # Add the flow to the switch
            self.ovs.add_flow(datapath, 10, match, actions)

            # Creating egress match and actions which will be send to ovs-switch
            match = parser.OFPMatch(
                    eth_type=switch['eth_type'],
                    in_port=(switch['out_port']),
                    ipv4_src=(route['ipv4_dst'], route['ipv4_dst_netmask']),
                    ipv4_dst=(route['ipv4_src'], route['ipv4_src_netmask'])
                )
            actions = [parser.OFPActionSetQueue(queue), parser.OFPActionOutput(switch['in_port'])]

            # Add the flow to the switch
            self.ovs.add_flow(datapath, 10, match, actions)

        print('worked, took',  + (time.time() - single)*1000, 'ms')
        return True, {'host': route['ipv4_dst']}


    def define_queue(self, route, datapath):
        connection = self.ovs.control[self.ovs.dpid_to_name[datapath.id]]
        queue = connection.create_queue(route)
        if 'max_rate' in route and route['max_rate'] is not None:
            connection.modify_default_queue(route['max_rate'])
        return queue

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        route = kwargs.get('route', None)
        print('delete s_id ', s_id, 'route ', route)

        # Check for validity of the slice ID
        if s_id not in self.slice_list:
            return False, 'Slice ID does not exist'

        # Check for validity of the route supposed to be deleted
        if not route:
            print('error: route not received, took',  + (time.time() - single)*1000, 'ms')
            return False, 'Missing route'
        

        # For each switch in the route
        for switch in route['switches']:
            # Extract the datapath parameters
            datapath = self.ovs.switches[switch['node']]
            dpid = datapath.id
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            direction = None
            if 'direction' in switch:
                direction = switch['direction']
            match_fw = parser.OFPMatch(
                    in_port=(switch['in_port']),
                    eth_type=switch['eth_type'],
                    ipv4_src=(route['ipv4_src'], route['ipv4_src_netmask']),
                    ipv4_dst=(route['ipv4_dst'], route['ipv4_dst_netmask'])
                )
            match_rv = parser.OFPMatch(
                    in_port=(switch['out_port']),
                    eth_type=switch['eth_type'],
                    ipv4_src=(route['ipv4_dst'], route['ipv4_dst_netmask']),
                    ipv4_dst=(route['ipv4_src'], route['ipv4_src_netmask'])
                )

            # Added this clause to verify if the flow rules should be 
            # deleted in the both directions
            if direction is None or direction == 'full':
                self.ovs.del_flow(datapath, match_fw)
                self.ovs.del_flow(datapath, match_rv)
            elif direction == 'half-fw':
                self.ovs.del_flow(datapath, match_fw)
            else:
                self.ovs.del_flow(datapath, match_rv)

        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': s_id}


class ovs_ctl(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ovs_ctl, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switches = {}
        
        self.dpid_to_name = {
            #  95536754289: 'h00',
            #  95535344413: 'h01',
            #  95542363502: 'h02'
            #95534111059: 'h00',
            #95538556217: 'h01',
            #95533205304: 'h02'
            95532435104: 's01',
            95533179799: 's02',
            95532162947: 's03',
            95539282496: 's04',
            95533558180: 's05'
        }

        self.topology = defaultdict(dict)
        self.topology['s01']['s02'] = 2
        self.topology['s02']['s01'] = 1
        self.topology['s01']['s03'] = 3
        self.topology['s03']['s01'] = 1
        self.topology['s02']['s05'] = 2
        self.topology['s05']['s02'] = 1
        self.topology['s03']['s04'] = 3
        self.topology['s04']['s03'] = 1
        self.topology['s04']['s05'] = 2
        self.topology['s05']['s04'] = 2

        self.speed = defaultdict(dict)
        self.speed['s01']['s02'] = 100
        self.speed['s02']['s01'] = 100
        self.speed['s01']['s03'] = 100
        self.speed['s03']['s01'] = 100
        self.speed['s02']['s05'] = 100
        self.speed['s05']['s02'] = 100
        self.speed['s03']['s04'] = 100
        self.speed['s04']['s03'] = 100
        self.speed['s04']['s05'] = 100
        self.speed['s05']['s04'] = 100

        self.ports = {}
        self.arp_disabled_ports = self.ports_to_disable()
        self.control = {}

        self.waiters = {}

        #  Instantiate the OVS SDR Controller
        self.ovs_controller_thread = ovs_controller(
            name='OVS',
            req_header='ovs_req', # Don't modify
            rep_header='ovs_rep', # Don't modify
            create_msg='wdc_crs',
            request_msg='wdc_rrs',
            update_msg='wdc_urs',
            delete_msg='wdc_drs',
            topology_msg='wdc_trs',
            host=kwargs.get('host', '10.0.0.5'),
            port=kwargs.get('port', 3300),
            ovs=self
        )

        # Start the OVS SDR Controller Server
        self.ovs_controller_hub = hub.spawn(self.ovs_controller_thread.run)

        self.count = 5
        self.st = time.time()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        single = time.time()
        # Get the new switch
        datapath = ev.msg.datapath
        # Add the new switch to the container 
        self.switches[self.dpid_to_name[datapath.id]] = datapath
        # Send proactive rules to the switches
        self._base_start(datapath)        
        self.count-= 1

        self.get_current_ports(datapath)
        self.connect_local_agent(datapath)
        print('took',  + (time.time() - single)*1000, 'ms')

        if (not self.count):
            print('total:', (time.time()-self.st)*1000, 'ms')

    def connect_local_agent(self, datapath):
        connection = nsb(datapath)
        connection.reset_queues()
        self.control[self.dpid_to_name[datapath.id]] = connection

    def ports_to_disable(self):
        stp = defaultdict(dict)
        nodes = list(self.topology.keys())
        visited = []
        stack = []
        stack.append(nodes[0])
        while stack:
          current = stack[0]
          if current not in visited:
            visited.append(current)
          next = list(self.topology[current].keys())
          for n in next:
            if n not in visited:
              stack.append(n)
              visited.append(n)
              stp[current][n] = self.topology[current][n]
              stp[n][current] = self.topology[n][current]
          stack.remove(current)

        b = {}
        for k in self.topology.keys():
          b[k] = []
          for l in list(self.topology.get(k).keys()):
            if l not in stp.get(k).keys():
              b[k].append(self.topology[str(k)][str(l)])
        return b


    def get_current_ports(self, datapath):
        dpid = datapath.id
        try:
            ofctl = supported_ofctl.get(datapath.ofproto.OFP_VERSION)
            desc = ofctl.get_port_desc(datapath, self.waiters)
        except Exception as e: 
            print(e)
            pass

    def _base_start(self, datapath):
        # Extract the datapath parameters
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Match all
        match = parser.OFPMatch({})
        
        # Delete all the existing flows
        self.del_flow(datapath, match)

        match = parser.OFPMatch()
        # Send and ask what to do to the controller
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]

        # Add the controller flow to the switch
        self.add_flow(datapath, 0, match, actions)

        # Output info message
        print('\t','Configured Switch ', self.dpid_to_name[dpid])

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def del_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
                datapath=datapath,
                match=match,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                command=ofproto.OFPFC_DELETE
            )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath 
        in_port = msg.match['in_port']
        parser = datapath.ofproto_parser

        dpid = datapath.id
        ofproto = datapath.ofproto

        pkt = packet.Packet(data=msg.data)

        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return

        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_icmp = pkt.get_protocol(icmp.icmp)

        #  self.logger.info("packet in %s %s %s %s",
        #  self.dpid_to_name[dpid],
        #  pkt_ethernet.src,
        #  pkt_ethernet.dst,
        #  in_port)

        if not pkt_arp:
            return


        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][pkt_ethernet.src] = in_port

        if pkt_ethernet.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][pkt_ethernet.dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        self.provision_paths(
                msg, in_port, pkt_ethernet.src, out_port, pkt_ethernet.dst, dpid)
            

    def provision_paths(self, msg, in_port, src, out_port, dst, dpid):
        parser = msg.datapath.ofproto_parser
        ofproto = msg.datapath.ofproto

        if out_port == ofproto.OFPP_FLOOD:
            if not self.ports or not self.arp_disabled_ports:
                return
            actions = []
            node = self.dpid_to_name.get(dpid)
            if node in self.ports:
                for port in self.ports[node]:
                    if port not in self.arp_disabled_ports[node] and port != in_port:
                        actions.append(parser.OFPActionOutput(port))
            else:
                return
        #  print(self.mac_to_port)

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            actions = [parser.OFPActionOutput(out_port)]

            match = parser.OFPMatch(
                    eth_type=0x0806, # 0x0806 = ARP packet
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src)

            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(msg.datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(msg.datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=msg.datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        msg.datapath.send_msg(out)


    @set_ev_cls([ofp_event.EventOFPStatsReply,
                 ofp_event.EventOFPDescStatsReply,
                 ofp_event.EventOFPFlowStatsReply,
                 ofp_event.EventOFPAggregateStatsReply,
                 ofp_event.EventOFPTableStatsReply,
                 ofp_event.EventOFPTableFeaturesStatsReply,
                 ofp_event.EventOFPPortStatsReply,
                 ofp_event.EventOFPQueueStatsReply,
                 ofp_event.EventOFPQueueDescStatsReply,
                 ofp_event.EventOFPMeterStatsReply,
                 ofp_event.EventOFPMeterFeaturesStatsReply,
                 ofp_event.EventOFPMeterConfigStatsReply,
                 ofp_event.EventOFPGroupStatsReply,
                 ofp_event.EventOFPGroupFeaturesStatsReply,
                 ofp_event.EventOFPGroupDescStatsReply,
                 ofp_event.EventOFPPortDescStatsReply
                 ], MAIN_DISPATCHER)
    def stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        body = msg.body

        if msg.type == 13:
            self.desc_stats_reply_handler(dp, body)

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        flags = 0
        if dp.ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION == ofproto_v1_2.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION >= ofproto_v1_3.OFP_VERSION:
            flags = dp.ofproto.OFPMPF_REPLY_MORE

        if msg.flags & flags:
            return
        del self.waiters[dp.id][msg.xid]
        lock.set()


    def desc_stats_reply_handler(self, dp, body):
        dpid = dp.id
        node = self.dpid_to_name.get(dpid)
        self.ports[node] = []
        for p in body:
            port = p.port_no
            if port != 4294967294:
                self.ports[node].append(port)
        print('Switch', node, ' ports:', self.ports[node])