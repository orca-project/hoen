#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event

import signal

class ServiceExit(Exception):
    pass


def signal_handler(sig, frame):
    # Raise ServiceExit upon call
    raise ServiceExit


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
        # Default CU Server host
        host = kwargs.get(self.host_key, self.default_host)
        # Default CU Server port
        port = kwargs.get(self.port_key, self.default_port)
        # Create a ZMQ context

        self.context = zmq.Context()
        #  Specity the type of ZMQ socket
        self.socket = self.context.socket(zmq.REQ)
        # Connect ZMQ socket to host:port
        self.socket.connect("tcp://" + host + ":" + str(port))


    def send_msg(**kwargs):
        # Inform the CU about the configuration success
        self.socket.send_json({self.request_key: kwargs})

        # Wait for command
        msg = self.socket.recv_json().get(self.reply_key, None)

        # Return the message (or None)
        return msg


class sdn_orch(orch_base):
    host_key = "sdn_host"
    port_key = "sdn_port"
    default_host = "127.0.0.1"
    default_port = "4000"
    request_key = "sdn_req"
    reply_key = "sdn_rep"


class sdr_orch(orch_base):
    host_key = "sdr_host"
    port_key = "sdr_port"
    default_host = "127.0.0.1"
    default_port = "5000"
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
        self.socket.bind("tcp://" + "127.0.0.1" + ":" + str(local_port))


    def run(self):
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Try to wait for command
            try:
                # Wait for command
                cmd = self.socket.recv_json(flags=zmq.NOBLOCK)

            # In case of ZMQ Error
            except zmq.ZMQError as e:
                # This means empty message
                if e.errno == zmq.EAGAIN:
                    # Wait for a second and try again
                    sleep(1)
                # Oh, this is serious
                else :
                    # Raise a real error
                    raise

            # Received a command
            else:
                # Service request, new service
                ns = cmd.get('sr_ns', None)

                # If the message worked
                if ns is not None:
                    print('- Create Service')
                    # Iterate over the list of configurations
                    for usrp in cu['configure']:
                        # Create the GRC
                        self.grc_handler.create_grc(**usrp)
                        # Consider the USRP busy
                        self.usrp_used.append(usrp['serial'])

                    # Inform the CU about the configuration success
                    self.socket.send_json({'cu_ack': {'id': str(self.uuid)}})

                # Service rerquest, remove service
                rs = cmd.get('sr_rs', None)

                 # If the flag exists
                if ru is not None:
                    print('- Remove Service')
                    # Iterate over the list of configurations
                    for usrp in ru['remove']:
                        # Remove the GRC
                        self.grc_handler.remove_grc(**usrp)
                        # Consider the USRP free
                        self.usrp_used.remove(usrp['serial'])

                    # Inform the CU about the removal success
                    self.socket.send_json({'ru_ack':{'id': str(self.uuid)}})


        # Terminate zmq
        self.socket.close()
        self.context.term()


if __name__ == "__main__":
    # Catch SIGTERM and SIGINT signals
    # signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start the Remote Unit Server
        hs_thread = hs_server(host='127.0.0.1', port=3000)
        hs_thread.start()

    except ServiceExit:
        # Terminate the RU Server
        ru_thread.shutdown_flag.set()
        print('Exitting')
