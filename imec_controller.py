#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import Signal
import signal

class ServiceExit(Exception):
    pass


def signal_handler(sig, frame):
    # Raise ServiceExit upon call
    raise ServiceExit


class imec_controller_server(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = []
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'imec_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'imec_rep')

        # Start the HS server
        self.server_bind(**kwargs)


    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('port', 6000)

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
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # IMEC: This is where you must create a radio slice

        # If succeeded creating the slice
        if True:
            # TODO We treat the radio slice as a network sink
            # Send ACK
            msg = {'nl_ack': {'host': "<IP>", "port": 6001}}

            # If failed creating slice
        else:
            # Send NACK
            msg = {'nl_nack': {'<Reason for failing>'}}

            # TODO You can use any logic you want. We just need the
            # resulting messages formatted like above

        return msg


    def remove_slice(self, **kwargs):
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # IMEC: This is where you must remove a radio slice

        # If succeeded removing the slice
        if True:
            # Send ACK
            msg = {'rl_ack': {'s_id': kwargs['s_id']}}

            # If failed removing slice
        else:
            # Send NACK
            msg = {'rl_nack': {'<Reason for failing>'}}

            # TODO You can use any logic you want. We just need the
            # resulting messages formatted like above



    def run(self):
        print('- Started IMEC Controller')
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Wait for command
            cmd = self.socket.recv_json()
            # IMEC SDR request
            imec_r = cmd.get(self.req_header, None)
            # If the message is valid
            if imec_r is not None:
                print('- Received Message')
                # Check wheter is it a new radio slice
                nl = imec_r.get('r_nl', None)

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
                    # Otherwise, it is a new service
                    else:
                        # Append it to the list of service IDs
                        self.s_ids.append(nl['s_id'])
                        print('\tService ID:', nl['s_id'])

                    # Create a readio slice
                    msg = self.create_slice(**nl)

                    # Send message
                    self.send_msg(self.rep_header, msg)

                # Check whether it is a removal
                rl = imec_r.get('r_rl', None)

                # If we must remove a radio slice
                if rl is not None:
                    print('- Remove Radio Slice')
                    # This service doesn't exist
                    if rl['s_id'] not in self.s_ids:
                        msg = {'dl_nack': 'The radio slice doesn\' exist:' +
                               rl['s_id']}

                        # Send message
                        self.send_message(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Otherwise, it is an existing service
                    else:
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
                self.send_message(self.rep_header, msg)



if __name__ == "__main__":
    # Catch SIGTERM and SIGINT signals
    # signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start the IMEC SDR Controller Server
        imec_controller_thread = imec_controller_server(
            host='127.0.0.1', port=6000)
        imec_controller_thread.start()

    except ServiceExit:
        # Terminate the IMEC SDR Controller Server
        imec_controller_thread.shutdown_flag.set()
        print('Exitting')
