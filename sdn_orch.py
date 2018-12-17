#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
# Import Signal
import signal

class ServiceExit(Exception):
    pass


def signal_handler(sig, frame):
    # Raise ServiceExit upon call
    raise ServiceExit



class sdn_server(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # Start the HS server
        self.server_bind(**kwargs)

    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('port', 5000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))

    def run(self):
        print('- Started SDN Orchestrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Wait for command wF
            cmd = self.socket.recv_json()
            print(cmd)

            # SDN request
            sdn_r = cmd.get('sdn_req', None)

            # If the message is valid
            if sdn_r is not None:
                print('- Received Message')
                # Check wheter is it a new core service
                ns = sdn_r.get('n_rs', None)

                # If it is a new core service
                if ns is not None:
                    print('- Create Core Service')
                    # TODO Instantiate it

                    # Reply
                    self.socket.send_json(
                        {'sdn_rep': {'host': "127.0.0.1",
                                     "port": 6001}})

                # If it is a remove core service
                rs = sdn_r.get('d_rs', None)

                if rs is not None:
                    print('- Remove Core Service')
                    # TODO Remove it

                    # Reply
                    self.socket.send_json(
                        {'sdn_rep': 'okidoki'})


            # If the flag exists
            else:
                print('- Failed to parse message')
                print('\tMessage:', cmd)


if __name__ == "__main__":
    # Catch SIGTERM and SIGINT signals
    # signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start the Remote Unit Server
        sdn_thread = sdn_server(host='127.0.0.1', port=5000)
        print('Start SDN Orchestrator')
        sdn_thread.start()

    except ServiceExit:
        # Terminate the RU Server
        sdn_thread.shutdown_flag.set()
        print('Exitting')
