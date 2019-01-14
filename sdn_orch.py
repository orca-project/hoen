#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
# Import OS
import os

import signal

def cls():
    os.system('cls' if os.name=='nt' else 'clear')


class ctl_base(object):
    name = ""
    host_key = ""
    port_key = ""
    default_host = "127.0.0.1"
    default_port = "6000"
    request_key = ""
    reply_key = ""

    def __init__(self, **kwargs):
         # Connect to the server
        self.server_connect(**kwargs)


    def server_connect(self, **kwargs):
        # Default Server host
        host = kwargs.get(self.host_key, self.default_host)
        # Default Server port
        port = kwargs.get(self.port_key, self.default_port)
        # Create a ZMQ context

        self.context = zmq.Context()
        #  Specity the type of ZMQ socket
        self.socket = self.context.socket(zmq.REQ)
        # Connect ZMQ socket to host:port
        self.socket.connect("tcp://" + host + ":" + str(port))


    def send_msg(self, kwargs):
        # Send request to the orchestrator
        self.socket.send_json({self.request_key: kwargs})
        # Wait for command
        msg = self.socket.recv_json().get(self.reply_key, None)
        # If the message is not valid
        if msg is None:
            # Return proper error
            return None, "Received invalid message: " + str(msg)
        # The orchestrator couldn't decode message
        elif 'msg_err' in msg:
            return None, msd['msg_err']
        # If failed creating a slice
        elif 'nl_nack' in msg:
            # Return the failure message
            return None, msg['nl_nack']
        # If succeeded creating a slice
        elif 'nl_ack' in msg:
            # Return host and port
            return msg['nl_ack']['host'], msg['nl_ack']['port']
        # If succeeded removing a slice
        elif 'rl_ack' in msg:
            # Return the Service ID  to confirm it
            return msg['rl_ack'], None
        # If failed removing a slice
        elif 'rl_nack' in msg:
            # Return the error message
            return None, msg['rl_nack']
        # Unexpected behaviour
        else:
            return None, "Missing ACK or NACK: " + str(msg)


    def create_core_slice(self, s_id, s_type):
        # Send creation message
        host, port = self.send_msg({'c_nl': {'type': s_type, 's_id': s_id}})

        # If the slice allocation failed
        if host is None:
            # Inform the hyperstrator about the failure
            print('\tFailed creating a Core Slice in ' + self.name)
            msg = {'ns_nack': port}

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\tSucceeded creating a Core Slice in ' + self.name)
            msg = {'ns_ack': {'host': host, 'port': port}}

        return msg


    def remove_core_slice(self, s_id, s_type):
        # Send removal message
        host, port = self.send_msg({'c_rl': {'type': s_type, 's_id': s_id}})

        # If the slice removal failed
        if host is None:
            # Inform the hyperstrator about the failure
            print('\tFailed removing a Core Slice in ' + self.name)
            msg = {'rs_nack': port}

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\tSucceeded removing a Core Slice in ' + self.name)
            msg = {'rs_ack': {'s_id': host}}

        return msg


class ovs_ctl(ctl_base):
    name = "OVS"
    host_key = "ovs_host"
    port_key = "ovs_port"
    default_host = "127.0.0.1"
    default_port = "9000"
    request_key = "ovs_req"
    reply_key = "ovs_rep"


class wired_orchestrator_server(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = {}
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'sdn_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'sdn_rep')

        # OVS Controller Handler
        self.ovs_ctl = ovs_ctl()

        # Start the HS server
        self.server_bind(**kwargs)


    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('port', 4000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

    def send_msg(self, message_header, message):
        # Send a message with a header
        self.socket.send_json({message_header: message})


    def run(self):
        print('- Started Wired Orchestrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

            try:
               # Wait for command
               cmd = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
               # Try again
               continue

            # SDN request
            sdn_r = cmd.get(self.req_header, None)
            # If the message is valid
            if sdn_r is not None:
                print('- Received Message')
                # Check wheter is it a new core service
                ns = sdn_r.get('r_ns', None)

                # If it is a new core service
                if ns is not None:
                    print('- Create Core Service')
                    # This service already exists
                    if ns['s_id'] in self.s_ids:
                        print('\tService ID already exists.')
                        msg = {'ns_nack': 'The service already exists: ' +
                               ns['s_id']}
                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue
                    # Otherwise, it is a new service
                    # Append it to the list of service IDs
                    self.s_ids[ns['s_id']] = ns.get('type', None)

                    print('\tService ID:', ns['s_id'])

                    # Send messate to OVS SDN Controller
                    print('\tDelegating it to the OVS Controller')

                    # Send the message to create a core slice
                    msg = self.ovs_ctl.create_core_slice(
                            ns['s_id'], ns['type'])

                    if False:
                        # Remove the service from the list of service IDs
                        del self.s_ids[ns['s_id']]

                    # Send message
                    self.send_msg(self.rep_header, msg)

                # If it is a remove core service
                rs = sdn_r.get('c_rs', None)

                if rs is not None:
                    print('- Remove Core Service')
                    # If this service doesn't exist
                    if rs['s_id'] not in self.s_ids:
                        print('\tService ID doesn\' exist')
                        msg = {'ds_nack': 'The service doesn\' exist:' +
                               rs['s_id']}

                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Send messate to OVS SDN Controller
                    print('\tDelegating it to the OVS Controller')

                    # Send message to remove core slice
                    msg = self.ovs_ctl.remove_core_slice(
                        rs['s_id'], self.s_ids[rs['s_id']])

                    if True:
                        # Remove the service from the list of service IDs
                        del self.s_ids[rs['s_id']]

                    # Send message
                    self.send_msg(self.rep_header, msg)

            # Failed to parse message
            else:
                print('- Failed to parse message')
                print('\tMessage:', cmd)

                msg = {'msg_err': "Failed to parse message:" + str(cmd)}
                # Send message
                self.send_msg(self.rep_header, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        wired_orchestrator_thread = wired_orchestrator_server(
            host='192.168.0.100', port=4000)
        wired_orchestrator_thread.start()

    except KeyboardInterrupt:
        # Terminate the Wired Orchestrator Server
        wired_orchestrator_thread.shutdown_flag.set()
        wired_orchestrator_thread.join()
        print('Exiting')
