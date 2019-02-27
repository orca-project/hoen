#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the Pause method of the Signal module
from signal import pause

class controller_base(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = []

        # Get the name from keyword arguments
        self.name = kwargs.get('name', 'CTL')

        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'ctl_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'ctl_rep')
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

         # Get the create slice message from keyword arguments
        self.create_msg = kwargs.get('create_msg', 'c_sl')
         # Get the create slice acknowledgment from keyword arguments
        self.create_ack = kwargs.get('create_ack', 'c_ack')
        # Get the create slice not acknowledgment from keyword arguments
        self.create_nack = kwargs.get('create_nack', 'c_nack')

        # Get the remove slice message from keyword arguments
        self.remove_msg = kwargs.get('remove_msg', 'r_sl')
         # Get the create slice acknowledgment from keyword arguments
        self.remove_ack = kwargs.get('remove_ack', 'r_ack')
        # Get the create slice not acknowledgment from keyword arguments
        self.remove_nack = kwargs.get('remove_nack', 'r_nack')

        # Start the controller server
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
        port = kwargs.get('port', 3000)

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

    def search_slice(self, **kwargs):
        # Must override this method
        pass

    def update_slice(self, **kwargs):
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

            # CTL request
            ctl_r = cmd.get(self.req_header, None)
            # If the message is valid
            if ctl_r is not None:
                print('- Received Message')
                # Check wheter is it a new slice
                create_slice = ctl_r.get(self.create_msg, None)

                # If we must create a new slice
                if create_slice is not None:
                    print('- Create Slice')
                    # This service already exists
                    if create_slice['s_id'] in self.s_ids:
                        print('\tService ID already exists.')
                        msg = {self.create_nack: 'The Slice already exists: ' +
                               create_slice['s_id']}
                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Append it to the list of service IDs
                    self.s_ids.append(create_slice['s_id'])
                    print('\tService ID:', create_slice['s_id'])

                    # Create new slice
                    msg = self.create_slice(**create_slice)
                    # Send message
                    self.send_msg(self.rep_header, msg)

                # Check whether it is a removal
                remove_slice = ctl_r.get(self.remove_msg, None)

                # If we must remove a slice
                if remove_slice is not None:
                    print('- Remove Slice')
                    # This service doesn't exist
                    if remove_slice['s_id'] not in self.s_ids:
                        msg = {self.remove_nack: 'The slice doesn\'t exist:' +
                               remove_slice['s_id']}

                        # Send message
                        self.send_message(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Remove it from the list of service IDs
                    self.s_ids.remove(remove_slice['s_id'])
                    print('\tService ID:', remove_slice['s_id'])

                    # Remove a slice
                    msg = self.remove_slice(**remove_slice)

                    # Send message
                    self.send_msg(self.rep_header, msg)


            # Failed to parse message
            else:
                print('- Failed to parse message')
                print('\tMessage:', cmd)

                msg = {self.error_msg: "Failed to parse message:" + str(cmd)}
                # Send message
                self.send_msg(self.rep_header, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()



if __name__ == "__main__":
    # Clear screen
    clear()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Template Controller thread
        template_controller_thread = controller_base(
            name='CTL',
            req_header='ctl_req',
            rep_header='ctl_rep',
            error_msg='msg_err',
            create_msg='c_sl',
            create_ack='c_ack',
            create_nack='c_nack',
            remove_msg='r_sl',
            remove_ack='r_ack',
            remove_nack='r_nack',
            host='127.0.0.1',
            port=3000)

        # Start the Template controller Thread
        template_controller_thread.start()
        # Pause the main thread
        pause()

    except KeyboardInterrupt:
        # Terminate the Wired Orchestrator Server
        ctl_controller_thread.shutdown_flag.set()
        ctl_controller_thread.join()
        print('Exiting')
