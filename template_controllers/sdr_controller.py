#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event

import signal

class sdr_controller_template(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = []

        # Get the name from keyword arguments
        self.name = kwargs.get('name', 'SDR')
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'sdr_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'sdr_rep')

        # Start the HS server
        self.server_bind(**kwargs)
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

        # Run post initialization operations
        self.post_init(**kwargs)


    def post_init(self, **kwargs):
        # Must overside this method
        pass

    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('port', 7000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))


    def send_msg(self, message_header, message):
        # Send a message with a header
        self.socket.send_json({message_header: message})


    def create_slice(self, **kwargs):
        # Must override this method
        pass


    def remove_slice(self, **kwargs):
        # Must overside this method
        pass



    def run(self):
        print('- Started ' + self.name + ' Controller')
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            try:
                # Wait for command
                cmd = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # SDR request
            sdr_r = cmd.get(self.req_header, None)
            # If the message is valid
            if sdr_r is not None:
                print('- Received Message')
                # Check wheter is it a new radio slice
                nl = sdr_r.get('r_nl', None)

                # If we must create a new radio slice
                if nl is not None:
                    print('- Create Radio Slice')
                    # This service already exists
                    if nl['s_id'] in self.s_ids:
                        print('\tService ID already exists.')
                        msg = {'nl_nack': 'The Radio Slice already exists: ' +
                               nl['s_id']}
                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Append it to the list of service IDs
                    self.s_ids.append(nl['s_id'])
                    print('\tService ID:', nl['s_id'])

                    # Create a readio slice
                    msg = self.create_slice(**nl)

                    # Send message
                    self.send_msg(self.rep_header, msg)

                # Check whether it is a removal
                rl = sdr_r.get('r_rl', None)

                # If we must remove a radio slice
                if rl is not None:
                    print('- Remove Radio Slice')
                    # This service doesn't exist
                    if rl['s_id'] not in self.s_ids:
                        msg = {'dl_nack': 'The radio slice doesn\'t exist:' +
                               rl['s_id']}

                        # Send message
                        self.send_message(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Remove it from the list of service IDs
                    self.s_ids.remove(rl['s_id'])
                    print('\tService ID:', rl['s_id'])

                    # Remove a Radio slice
                    msg = self.remove_slice(**rl)

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
    clear()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the SDR Controller Server
        sdr_controller_thread = sdr_controller_template(
            host='127.0.0.1', port=7000)
        sdr_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wired Orchestrator Server
        sdr_controller_thread.shutdown_flag.set()
        sdr_controller_thread.join()
        print('Exiting')
