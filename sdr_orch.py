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



class sdr_server(Thread):

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
        port = kwargs.get('port', 4000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))

    def run(self):
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Wait for command wF
            cmd = self.socket.recv_json()
            print(cmd)

            # SDR request
            sdr_r = cmd.get('sdr_req', None)

            # If the message is valid
            if sdr_r is not None:
                print('- Received Message')
                # Check wheter is it a new radio service
                ns = sdr_r.get('n_rs', None)

                # If it is a new radio service
                if ns is not None:
                    print('- Create Radio Service')
                    # TODO Instantiate it

                    # Reply
                    self.socket.send_json(
                        {'sdr_rep': {'host': "127.0.0.1",
                                     "port": 5001}})

                # If it is a remove radio service
                rs = sdr_r.get('d_rs', None)

                if rs is not None:
                    print('- Remove Radio Service')
                    # TODO Remove it

                    # Reply
                    self.socket.send_json(
                        {'sdr_rep': 'okidoki'})


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
        sdr_thread = sdr_server(host='127.0.0.1', port=4000)
        print('Start SDR Orchestrator')
        sdr_thread.start()

    except ServiceExit:
        # Terminate the RU Server
        sdr_thread.shutdown_flag.set()
        print('Exitting')
