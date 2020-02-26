#!/usr/bin/env python3

# Import the ZMQ module
from eventlet.green import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the Pause method of the Signal module
from signal import pause

class base_controller(object):

    def __init__(self, **kwargs):
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = []

        # Get the name from keyword arguments
        self.name = kwargs.get('name', 'CTL')

        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Start the controller server
        self._server_bind(**kwargs)

        # Run post initialization operations
        self.post_init(**kwargs)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'ctl_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'ctl_rep')
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

         # Get the create slice message from keyword arguments
        self.create_msg = kwargs.get('create_msg', 'ct_cs')
         # Get the create service acknowledgment from keyword arguments
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        # Get the request service message from keyword arguments
        self.request_msg = kwargs.get('request_msg', 'ct_rs')
         # Get the create service acknowledgment from keyword arguments
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        # Get the remove service message from keyword arguments
        self.update_msg = kwargs.get('update_msg', 'ct_us')
         # Get the create service acknowledgment from keyword arguments
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        # Get the remove service message from keyword arguments
        self.delete_msg = kwargs.get('delete_msg', 'ct_ds')
         # Get the create service acknowledgment from keyword arguments
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

        # Get the topology message from keyword arguments
        self.topology_msg = kwargs.get('topology_msg', 'ct_ts')
        self.topology_ack = "_".join([self.topology_msg.split('_')[-1], "ack"])
        self.topology_nack = "_".join([self.topology_msg.split('_')[-1], "nack"])


    def _post_init(self, **kwargs):
        # Must overside this method
        pass


    def _server_bind(self, **kwargs):
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
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)


    def _send_msg(self, message_type, message):
        # Send a message with a header
        self.socket.send_json({self.rep_header: {message_type: message}})


    def create_slice(self, **kwargs):
        # Must override this method
        pass

    def request_slice(self, **kwargs):
        # Must override this method
        pass

    def update_slice(self, **kwargs):
        # Must override this method
        pass

    def delete_slice(self, **kwargs):
        # Must overside this method
        pass

    def get_topology(self, **kwargs):
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
            request = cmd.get(self.req_header, None)
            # If the message is valid
            if request is not None:
                print('- Received Message')
                # Check wheter is it a new slice
                create_slice = request.get(self.create_msg, None)

                # If we must create a new slice
                if create_slice is not None:
                    print('- Create Slice')
                    # This service already exists
                    '''if create_slice['s_id'] in self.s_ids:
                        print('\tService ID already exists.')
                        msg = 'The Slice already exists: ' + \
                            create_slice['s_id']
                        # Send message
                        self._send_msg(self.create_nack, msg)
                        # Leave if clause
                        continue
                    '''

                    # Append it to the list of service IDs
                    self.s_ids.append(create_slice['s_id'])
                    print('\t', 'Service ID:', create_slice['s_id'])

                    # Create new slice
                    success, msg = self.create_slice(**create_slice)
                    # Send message
                    self._send_msg(self.create_ack if success else \
                                   self.create_nack, msg)

                # Check whether it is a removal
                delete_slice = request.get(self.delete_msg, None)

                # If we must delete a slice
                if delete_slice is not None:
                    print('- Delete Slice')
                    # This service doesn't exist
                    if delete_slice['s_id'] not in self.s_ids:
                        msg = 'The slice does not exist:' + \
                            delete_slice['s_id']

                        # Send message
                        self._send_msg(self.delete_nack, msg)
                        # Leave if clause
                        continue

                    # Remove it from the list of service IDs
                    self.s_ids.remove(delete_slice['s_id'])
                    print('\t', 'Service ID:', delete_slice['s_id'])

                    # Remove a slice
                    success, msg = self.delete_slice(**delete_slice)

                    # Send message
                    self._send_msg(self.delete_ack if success else \
                                   self.delete_nack, msg)

                # Check whether it is a topology check
                get_topology = request.get(self.topology_msg, None)

                # If we must retrieve the network topology
                if get_topology is not None:
                    print('- Get Topology')
                    success, msg = self.get_topology(**get_topology)
                    # Send message
                    self._send_msg(self.topology_ack if success else \
                                   self.topology_nack, msg)

                # Check for unknown messages
                unknown_msg = [x for x in request if x not in [self.create_msg,
                                                               self.request_msg,
                                                               self.update_msg,
                                                               self.delete_msg,
                                                               self.topology_msg]]
                # If there is at least an existing unknown message
                if unknown_msg:
                    print('- Unknown message')
                    print('\t', 'Message:', unknown_msg[0])

                    msg = "Unknown message: " + str(unknown_msg[0])
                    # Send message
                    self._send_msg(self.error_msg, msg)

            # Failed to parse message
            else:
                print('- Failed to parse message')
                print('\t', 'Message:', request)

                msg = "Failed to parse message: " + str(request)
                # Send message
                self._send_msg(self.error_msg, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()



if __name__ == "__main__":
    # Clear screen
    clear()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Base Controller
        template_controller_thread = base_controller(
            name='CTL',
            req_header='ctl_req',
            rep_header='ctl_rep',
            error_msg='msg_err',
            create_msg='tc_cs',
            request_msg='tc_rs',
            update_msg='tc_us',
            delete_msg='tc_ds',
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
