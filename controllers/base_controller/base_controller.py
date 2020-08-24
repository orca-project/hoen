#!/usr/bin/env python3

# Import the environ object from the OS module
from os import environ, system, name
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the Pause method of the Signal module
from signal import pause
# Import the time method from the time module
from time import time
# Import the format exception method from the traceback module
from traceback import format_exc

# Check which ZMQ we should load
if "EVENTLET_ZMQ" not in environ:
    # Import the original ZMQ module
    import zmq
else:
    # Import Eventlet's ZMQ modules
    from eventlet.green import zmq

# Received delay of 10 sec
RECV_DELAY = 30*1000

def cls():
    system('cls' if name=='nt' else 'clear')


class base_controller(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # Container to hold the list of Service IDs
        self.s_ids = {}

        # Get the name from keyword arguments
        self.name = kwargs.get('name', 'CTL')

        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Start the controller server
        self._server_bind(**kwargs)

        # Print start up message
        self._log('Started ' + self.name + ' Controller', head=True)
        # Run post initialization operations
        self.post_init(**kwargs)


    # Make printing easier. TODO: Implement real logging
    def _log(self, *args, head=False):
        print("-" if head else '\t' ,*args)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'ctl_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'ctl_rep')
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

         # Get the network info message from keyword arguments
        self.info_msg = kwargs.get('info_msg', 'ct_ni')
         # Get the network info acknowledgment from keyword arguments
        self.info_ack = "_".join([self.info_msg.split('_')[-1], "ack"])
        # Get the network info  not acknowledgment from keyword arguments
        self.info_nack = "_".join([self.info_msg.split('_')[-1], "nack"])

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

    def post_init(self, **kwargs):
        # Must override this method
        pass

    def pre_exit(self):
        # Must override this method
        pass

    def _server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '0.0.0.0')
        # Default HS Server port
        port = kwargs.get('port', 3000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, RECV_DELAY)


    def _send_msg(self, message_type, message):
        # Send a message with a header
        self.socket.send_json({self.rep_header: {message_type: message}})

    def network_info(self, **kwargs):
        # Must override this method
        pass

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
        # Must override this method
        pass

    def get_topology(self, **kwargs):
        # Must override this method
        pass

    def run(self):
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            try:
                # Wait for command
                cmd = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # Keep track of time
            st = time()
            # Controller transaction
            transaction = cmd.get(self.req_header, None)
            # If the message is valid
            if transaction is not None:
                self._log('Received Message', head=True)

                # Check whether we should get information about the segment
                network_info = transaction.get(self.info_msg, None)

                # If we are getting information about the network segment
                if network_info is not None:
                    self._log('Get information from the', self.name, head=True)
                    try:
                        # Create new slice
                        success, msg = self.network_info(**network_info)
                    except Exception:
                        success = False
                        msg = str(format_exc())

                    # Log event
                    self._log("Obtained information"if success else \
                        "Failed obtaining information", 'Took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.info_ack if success else \
                                   self.info_nack, msg)

                # Check whether is it a new slice
                create_slice = transaction.get(self.create_msg, None)

                # If we must create a new slice
                if create_slice is not None:
                    self._log('Create Slice', head=True)
                    # This service already exists
                    if create_slice['s_id'] in self.s_ids:
                        self._log('Service ID already exists.')
                        msg = 'The Slice already exists: ' + \
                            create_slice['s_id']
                        # Send message
                        self._send_msg(self.create_nack, msg)
                        # Leave if clause
                        continue

                    # Append it to the list of service IDs
                    self.s_ids[create_slice['s_id']] = {}
                    self._log('Service ID:', create_slice['s_id'])

                    try:
                        # Create new slice
                        success, msg = self.create_slice(**create_slice)
                    except Exception:
                        success = False
                        msg = str(format_exc())
                        del self.s_ids[create_slice['s_id']]

                    # In case of issues for creating slices
                    if not success:
                        self.s_ids.pop(create_slice['s_id'], None)

                    # Log event
                    self._log("Created Slice" if success else \
                        "Failed  creating Slice", 'Took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.create_ack if success else \
                                   self.create_nack, msg)

                # If it is a request service
                request_slice = transaction.get(self.request_msg, None)

                if request_slice is not None:
                    self._log('Request Slice', head=True)
                    # If missing the slice ID:
                    if 's_id' not in request_slice:
                        self._log("Missing Service ID.")
                        # Send message
                        self._send_msg(self.request_nack, "Missing Service ID")
                        # Leave if clause
                        continue

                    # If there is an S_ID but it doesn't exist
                    elif request_slice['s_id'] and \
                            (request_slice['s_id'] not in self.s_ids):
                        self._log('The slice does not exist')
                        # Send message
                        self._send_msg(self.request_nack,
                                      'The slice does not exist: ' + \
                                      request_slice['s_id'])
                        # Leave if clause
                        continue

                    # If gathering information about a slice
                    if request_slice['s_id']:
                        self._log('Service ID:', request_slice['s_id'])
                   # If set to gather information about all slices
                    else:
                        self._log('Gather information about all Service IDs')

                    try:
                        # Request a slice
                        success, msg = self.request_slice(**request_slice)
                    except Exception:
                        success = False
                        msg = str(format_exc())

                    # Log event
                    self._log("Requested Slice" if success else \
                        "Failed requesting Slice", 'Took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.request_ack if success else \
                                   self.request_nack, msg)

                # Update slice transaction
                update_slice = transaction.get(self.update_msg, None)

                # If the flag exists
                if update_slice is not None:
                    self._log('Update Slice Transaction', head=True)

                    self._log("Not implemented yet.")

                    continue

                # Check whether it is a removal
                delete_slice = transaction.get(self.delete_msg, None)

                # If we must delete a slice
                if delete_slice is not None:
                    self._log('Delete Slice', head=True)
                    # This service doesn't exist
                    if delete_slice['s_id'] not in self.s_ids:
                        msg = 'The slice does not exist:' + \
                            delete_slice['s_id']

                        # Send message
                        self._send_msg(self.delete_nack, msg)
                        # Leave if clause
                        continue

                    self._log('Service ID:', delete_slice['s_id'])

                    try:
                        # Remove a slice
                        success, msg = self.delete_slice(**delete_slice)
                    except Exception:
                        success = False
                        msg = str(format_exc())

                    # Log event
                    self._log("Deleted Slice" if success else \
                        "Failed deleting Slice", 'Took:',
                              (time() - st)*1000, 'ms')

                    # If deleted the slice
                    if success:
                        # Remove it from the list of service IDs
                        del self.s_ids[delete_slice['s_id']]

                    # Send message
                    self._send_msg(self.delete_ack if success else \
                                   self.delete_nack, msg)

                # Check whether it is a topology check
                get_topology = transaction.get(self.topology_msg, None)

                # If we must retrieve the network topology
                if get_topology is not None:
                    self._log('Get Topology', head=True)

                    success, msg = self.get_topology(**get_topology)
                    # Send message
                    self._send_msg(self.topology_ack if success else \
                                   self.topology_nack, msg)

                # Check for unknown messages
                unknown_msg = [x for x in transaction if x not in [
                    self.create_msg, self.request_msg,
                    self.update_msg, self.delete_msg,
                    self.info_msg, self.topology_msg]]

                # If there is at least an existing unknown message
                if unknown_msg:
                    self._log('Unknown message', head=True)
                    self._log('Message:', unknown_msg[0])

                    msg = "Unknown message: " + str(unknown_msg[0])
                    # Send message
                    self._send_msg(self.error_msg, msg)

            # Failed to parse message
            else:
                self._log('Failed to parse message', head=True)
                self._log('Message:', transaction)

                msg = "Failed to parse message: " + str(transaction)
                # Send message
                self._send_msg(self.error_msg, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()

    # Method for stopping the server thread nicely
    def safe_shutdown(self):
        self._log("Exiting", head=True)
        self.shutdown_flag.set()
        self.pre_exit()
        self.join()


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
            info_msg='tc_ni',
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
        ctl_controller_thread.safe_shutdown()
