#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the uuid4 function from the UUID module
from uuid import uuid4
# Import the sleep function from the time module
from time import sleep
# Import OS
import os

import signal

def cls():
    os.system('cls' if os.name=='nt' else 'clear')


class orch_base(object):
    host_key = ""
    port_key = ""
    default_host = "127.0.0.1"
    default_port = "3000"
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
        # If the create slice request succeeded
        elif 'ns_ack' in msg:
            # Return host and port
            return msg['ns_ack']['host'], msg['ns_ack']['port']
        # If the create slice request failed
        elif 'ns_nack' in msg:
            # Return the failure message
            return None, msg['ns_nack']
        # If the remove slice request succeeded
        elif 'rs_ack' in msg:
            # Return the Service ID to confirm it
            return msg['rs_ack'], None
         # If the remove slice request failed
        elif 'rs_nack' in msg:
            # Return the failure message
            return None, msg['rs_nack']
        # Unexpected behaviour
        else:
            return None, "Missing ACK or NACK: " + str(msg)


class sdn_orch(orch_base):
    host_key = "sdn_host"
    port_key = "sdn_port"
    default_host = "192.168.0.100"
    default_port = "5000"
    request_key = "sdn_req"
    reply_key = "sdn_rep"


class sdr_orch(orch_base):
    host_key = "sdr_host"
    port_key = "sdr_port"
    default_host = "192.168.0.100"
    default_port = "4000"
    request_key = "sdr_req"
    reply_key = "sdr_rep"


class hs_server(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)

        # Flat to exit gracefully
        self.shutdown_flag = Event()

        # Start the HS server
        self.server_bind(**kwargs)

        # Container to hold the list of current services
        self.s_ids = []

        # Create an instance of the SDN orchestrator handler
        self.sdn_orch = sdn_orch()
        # Create an instance of the SDR orchestrator handler
        self.sdr_orch = sdr_orch()


    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('hs_host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('hs_port', 3000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

    def run(self):
        print('- Started Hyperstrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

             try:
                # Wait for command
                cmd = self.socket.recv_json()
             # If nothing was received during the timeout
             except zmq.Again:
                # Try again
                continue

             # Received a command
             else:
                # Service request, new service
                ns = cmd.get('sr_ns', None)

                # If the message worked
                if ns is not None:
                    print('- Create Service Request')
                    # Create a Service ID
                    s_id = str(uuid4())

                    print('\tService ID:', s_id)
                    print('\tSend message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    r_host, r_port = self.sdr_orch.send_msg(
                        {"r_ns": {'type': ns['type'], 's_id': s_id}})

                    # If the radio allocation failed
                    if r_host is None:
                        # Inform the user about the failure
                        self.socket.send_json({'ns_nack': r_port})
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\tSucceeded creating a Radio Service')

                    # TODO For the future, SDN hooks
                    if False:
                        # Otherwise, send message to the SDN orchestrator
                        c_host, c_port = self.sdn_orch.send_msg(
                            {"c_ns": {'type': ns['type'], 's_id': s_id,
                                      'destination': (r_host, r_port),
                                      'source': ('127.0.0.1', 6000)
                            }})

                    # TODO if the wired and the wireless parts worked
                    # Append it to the list of service IDs
                    self.s_ids.append(s_id)

                    # Inform the user about the configuration success
                    # TODO the host and port should come from the SDN orch.
                    self.socket.send_json({'ns_ack': {'s_id': s_id,
                                                      'host': r_host,
                                                      "port": r_port}})

                # Service rerquest, remove service
                rs = cmd.get('sr_rs', None)

                 # If the flag exists
                if rs is not None:
                    print('- Remove Service Request')
                    # If this service doesn't exist
                    if rs['s_id'] not in self.s_ids:
                        print('\tService ID doesn\' exist')
                        # Send message
                        self.socket.send_json(
                            {'rs_nack': 'The service doesn\'t exist:' +
                             rs['s_id']})

                        # Leave if clause
                        continue

                    print('\tService ID:', rs['s_id'])
                    print('\tSend message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    r_host, r_port = self.sdr_orch.send_msg(
                        {"r_rs": {'s_id': rs['s_id']}})

                    # If the radio removal failed
                    if r_host is None:
                        # Inform the user about the failure
                        self.socket.send_json({'rs_nack': r_port})
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\tSucceeded removing a Radio Service')

                    # TODO For the future, SDN hooks
                    if False:
                        # Otherwise, send message to the SDN orchestrator
                        c_host, c_port = self.sdn_orch.send_msg(
                            {"c_rs": {'s_id': rs['s_id']}})

                    # TODO if the wired and the wireless parts worked
                    # Remove it to the list of service IDs
                    self.s_ids.remove(rs['s_id'])

                    # Inform the user about the removal success
                    self.socket.send_json({'rs_ack': {'s_id': rs['s_id']}})

        # Terminate zmq
        self.socket.close()
        self.context.term()


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        hs_thread = hs_server(host='127.0.0.1', port=3000)
        hs_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Hyperstrator
        hs_thread.shutdown_flag.set()
        hs_thread.join()
        print('Exiting')
