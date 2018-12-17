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
        # COntainer to hold the list of Service IDs
        self.s_ids = []
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'sdr_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'sdr_rep')
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


    def send_msg(self, message_header, message):
        # Send a message with a header
        self.socket.send_json({message_header: message})


    def run(self):
        print('- Started SDR Orchestrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Wait for command
            cmd = self.socket.recv_json()
            # SDR request
            sdr_r = cmd.get(self.req_header, None)
            # If the message is valid
            if sdr_r is not None:
                print('- Received Message')
                # Check wheter is it a new radio service
                ns = sdr_r.get('r_ns', None)

                # If it is a new radio service
                if ns is not None:
                    print('- Create Radio Service')
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
                    else:
                        # Append it to the list of service IDs
                        self.s_ids.append(ns['s_id'])
                        print('\tService ID:', ns['s_id'])

                    # Decide what to do based on the type of traffic
                    if ns['type'] == "high-throughput":
                        # Send message to TCD SDR controller
                        print('\tTraffic type: High Throughput')
                        # Send ACK
                        msg = {'ns_ack': {'host': "127.0.0.1", "port": 5001}}


                    elif ns['type'] == "low-latency":
                        # Send messate to IMEC SDR Controller
                        print('\tTraffic type: Low Latency')
                        # Send ACK
                        msg = {'ns_ack': {'host': "127.0.0.1", "port": 5002}}


                    # Otherwise, couldn't identify the traffic type
                    else:
                        print('\tInvalid traffic type.')
                        # Send NACK
                        msg = {'ns_nack':
                               'Couldn\'t identify the traffic type:' +
                              str(ns['type'])}

                    # Send message
                    self.send_msg(self.rep_header, msg)

                # If it is a remove radio service
                rs = sdr_r.get('r_rs', None)

                if rs is not None:
                    print('- Remove Radio Service')
                    # This service doesn't exist
                    if ns['s_id'] not in self.s_ids:
                        msg = {'ds_nack': 'The service doesn\' exist:' +
                               ns['s_id']}

                        # Send message
                        self.send_message(self.rep_header, msg)
                        # Leave if clause
                        break
                    # Otherwise, it is a new service
                    else:
                        # Append it to the list of service IDs
                        self.s_ids.remove(ns['s_id'])


                    # Decide what to do based on the type of traffic
                    if ns['type'] == "high-throughput":
                        # Send message to TCD SDR controller
                        print('\tTraffic type: High Throughput')
                        # Send ACK
                        msg = {'rs_ack': {'host': "127.0.0.1", "port": 5001}}


                    elif ns['type'] == "low-latency":
                        # Send messate to IMEC SDR Controller
                        print('\tTraffic type: Low Latency')
                        # Send ACK
                        msg = {'rs_ack': {'host': "127.0.0.1", "port": 5002}}


                    # Otherwise, couldn't identify the traffic type
                    else:
                        # Send NACK
                        msg = {'rs_nack':
                               'Couldn\'t identify the traffic type:' +
                               str(rs['type'])}

                    # Send message
                    self.send_message(self.rep_header, msg)

            # Failed to parse message
            else:
                print('- Failed to parse message')
                print('\tMessage:', cmd)

                msg = {'msg_err': "Failed to parse message:" + str(cmd)}
                # Send message
                self.send_message(self.rep_header, msg)



if __name__ == "__main__":
    # Catch SIGTERM and SIGINT signals
    # signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start the Remote Unit Server
        sdr_thread = sdr_server(host='127.0.0.1', port=4000)
        sdr_thread.start()

    except ServiceExit:
        # Terminate the RU Server
        sdr_thread.shutdown_flag.set()
        print('Exitting')
