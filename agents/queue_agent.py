#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the uuid4 function from the UUID module
from uuid import uuid4
# Import the system method from the OS module
from os import system, name
# Import the Pause method from the Signal module
from signal import pause

import time
import subprocess

def cls():
    system('cls' if name == 'nt' else 'clear')

class queue_agent_server(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)

        self.shutdown_flag = Event()
        self._server_bind(host, port)

    # Bind server to socket
    def _server_bind(self, host, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://" + host + ":" + str(port))
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

    def send_msg(self, message):
        # Send a message with a header
        self.socket.send_json(message)

    def run(self):
        print('- Started Queue agent')
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
                resp = []
                for operation in request:
                    if operation.get('type') == 'reset_req':
                        r = self.call_reset_service(operation)
                        resp.append(r)
                    elif operation.get('type') == 'create_req':
                        r = self.call_create_service(operation)
                        resp.append(r)
                    elif operation.get('type') == 'modify_req':
                        r = self.call_modify_service(operation)
                        resp.append(r)
                    else:
                        r = {
                                "id": t_id,
                                "type": "reset_resp",
                                "result_code": 1
                            }
                        resp.append(r)
                self.send_msg(resp)

        # Terminate zmq
        self.socket.close()
        self.context.term()

    def call_reset_service(self, operation):
        t_id = operation.get('t_id')
        min_rate = operation.get('default_queue').get('min_rate')
        max_rate = operation.get('default_queue').get('max_rate')
        priority = operation.get('default_queue').get('priority')

        count = 0
        total = 0
        default_qos = {}
        default_queue = {}
        destroy_command = 'for p in `ovs-vsctl list port | grep name | cut -d":" -f2 | sed "s/ //g" | sed "s/\\"//g"` ;do ovs-vsctl clear port $p qos ;done; ovs-vsctl --all destroy qos ; ovs-vsctl --all destroy queue'
        (c1, o1) = self.run_system_command(destroy_command)
        if c1 == 0:
            ports = self.map_ports()
            total = len(ports)
            for port in ports:
                create_qos_command = 'ovs-vsctl create qos type=linux-htb other-config:max-rate=10000000000'
                (c2, o2) = self.run_system_command(create_qos_command)

                if c2 == 0:
                    default_qos[port] = o2
                    add_qos_to_ports_command = 'ovs-vsctl set port ' + port + ' qos=' + o2
                    (c3, o3) = self.run_system_command(add_qos_to_ports_command)

                    if c3 == 0:
                        create_default_queue_command = 'ovs-vsctl create queue other-config:min-rate=' + str(min_rate) + ' other-config:max-rate=' + str(max_rate) + ' other-config:priority=' + str(priority)
                        (c4, o4) = self.run_system_command(create_default_queue_command)

                        if c4 == 0:
                            default_queue[port] = self.create_queue_object(ports[port], o4, min_rate, max_rate, priority)
                            add_default_queue_to_qos_command = 'ovs-vsctl set qos ' + o2 + ' queues=' + str(ports[port]) + '=' + o4
                            (c5, o5) = self.run_system_command(add_default_queue_to_qos_command)
                            if c5 == 0:
                                count = count + 1


        if count == total:
            resp = {
                    "t_id": t_id,
                    "type": "reset_resp",
                    "result_code": 0,
                    "default_qos": default_qos,
                    "default_queue": default_queue,
                    "ports": ports
                  }
        else:
            self.run_system_command(destroy_command)
            resp = {
                    "t_id": t_id,
                    "type": "reset_resp",
                    "result_code": 1
                  }
        return resp

    def call_create_service(self, operation):
        t_id = operation.get('t_id')
        qos = operation.get('qos')
        q_id = operation.get('queue').get('q_id')
        min_rate = operation.get('queue').get('min_rate')
        max_rate = operation.get('queue').get('max_rate')
        priority = operation.get('queue').get('priority')
        result_code = 1

        create_queue_command = 'ovs-vsctl create queue'
        if min_rate is not None:
            create_queue_command = create_queue_command + ' other-config:min-rate='+ str(min_rate)
        if max_rate is not None:
            create_queue_command = create_queue_command + ' other-config:max-rate='+ str(max_rate)
        if priority is not None:
            create_queue_command = create_queue_command + ' other-config:priority='+ str(priority)

        (c1, o1) = self.run_system_command(create_queue_command)

        if c1 == 0:
            add_default_queue_to_qos_command = 'ovs-vsctl set qos ' + qos + ' queues:' + str(q_id) + '=' + o1
            (c2, o2) = self.run_system_command(add_default_queue_to_qos_command)
            if c2 == 0:
                result_code = 0

        if result_code == 0:
            resp = {
                    "t_id": t_id,
                    "type": "create_resp",
                    "result_code": result_code,
                    "queue": {
                      "q_id": q_id,
                      "uuid": o1
                    }
                  }
        else:
            resp = {
                    "t_id": t_id,
                    "type": "create_resp",
                    "result_code": result_code
                  }
        return resp

    def call_modify_service(self, operation):
        # ovs-vsctl set queue b0a5449d-e078-4528-9ba6-aa28b865a507 other-config:max-rate=83886080
        t_id = operation.get('t_id')
        uuid = operation.get('queue').get('uuid')
        min_rate = operation.get('queue').get('min_rate')
        max_rate = operation.get('queue').get('max_rate')
        priority = operation.get('queue').get('priority')
        result_code = 1
        command = 'ovs-vsctl set queue ' + uuid
        if min_rate is not None:
            command = command + ' other-config:min-rate='+ str(min_rate)
        if max_rate is not None:
            command = command + ' other-config:max-rate='+ str(max_rate)
        if priority is not None:
            command = command + ' other-config:priority='+ str(priority)
        (result_code, out) = self.run_system_command(command)

        resp = {
                "t_id": t_id,
                "type": "modify_resp",
                "result_code": result_code
              }
        return resp

    def run_system_command(self, command):
        print(command)
        resp =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        resp.wait()
        out = resp.stdout.read().decode().strip()
        code = resp.returncode
        return code, out

    def map_ports(self):
        command = 'ovs-vsctl --columns=name,ofport list Interface'
        (c1, o1) = self.run_system_command(command)
        lines = o1.split('\n')
        flag = 0
        ports = {}
        for line in lines:
          if len(line.split(': ')) > 1:
            if flag == 0:
              name = line.split(': ')[1].replace('"', '')
              ports[name] = None
              flag = 1
            else:
              port_no = line.split(': ')[1]
              ports[name] = int(port_no)
              flag = 0
        #p = dict(zip(ports.values(),ports.keys()))
        return ports

    def create_queue_object(self, q_id, uuid, min_rate, max_rate, priority):
        return {
                  "q_id": q_id,
                  "uuid": uuid,
                  "min_rate": min_rate,
                  "max_rate": max_rate,
                  "priority": priority
                }

if __name__ == "__main__":
    cls()

    try:
        host = '0.0.0.0'
        port = 4400
        queue_agent_thread = queue_agent_server(host, port)
        queue_agent_thread.start()
        pause()

    except KeyboardInterrupt:
        queue_agent_thread.shutdown_flag.set()
        queue_agent_thread.join()
        print('Exiting')
