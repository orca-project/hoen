#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread, Lock and Event objects from the threading module
from threading import Thread, Lock, Event
# Import the uuid4 function from the UUID module
from uuid import uuid4
# Import the system method from the OS module
from os import system, name
# Import the Pause method from the Signal module
from signal import pause
# Import the Time method from the Time module
from time import time

# Received delay of 10 sec
RECV_DELAY = 30*10000

# Clear terminal screen
def cls():
    # Perform action based on the current platform
    system('cls' if name == 'nt' else 'clear')


class orch_base(object):
    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        self.name = kwargs.get("name", "")
        self.type = kwargs.get('type', '')
        self.host_key = kwargs.get("host_key", "")
        self.port_key = kwargs.get("port_key", "")
        self.default_host = kwargs.get("default_host", "127.0.0.1")
        self.default_port = kwargs.get("default_port", "3000")
        self.request_key = kwargs.get("request_key", "")
        self.reply_key = kwargs.get("reply_key", "")

        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Connect to the server
        self._server_connect(**kwargs)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get("error_msg", "msg_err")

        self.create_msg = kwargs.get("create_msg", "bo_crs")
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        self.request_msg = kwargs.get("request_msg", "bo_rrs")
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        self.update_msg = kwargs.get("update_msg", "bo_urs")
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        self.delete_msg = kwargs.get("delete_msg", "bo_drs")
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

    def _server_connect(self, **kwargs):
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
        # Timeout reception every 5 seconds
        self.socket.setsockopt(zmq.RCVTIMEO, RECV_DELAY)
        # # Allow multiple requests and replies
        self.socket.setsockopt(zmq.REQ_RELAXED, 1)
        # # Add IDs to ZMQ messages
        self.socket.setsockopt(zmq.REQ_CORRELATE, 1)

    def _send_msg(self, ack, nack, **kwargs):
        # Send request to the orchestrator
        self.socket.send_json({self.request_key: kwargs})

        try:
            # Wait for command
            msg = self.socket.recv_json().get(self.reply_key, None)

        # If nothing was received during the timeout
        except zmq.Again:
            # Try again
            return False, "Connection timeout to " + self.name + " Orchestrator"

        # If the message is not valid
        if msg is None:
            # Return proper error
            return False, "Received invalid message: " + str(msg)
        # The orchestrator couldn't decode message
        elif self.error_msg in msg:
            # Return message and error code
            return False, msg[self.error_msg]
        # If the request succeeded
        elif ack in msg:
            # Return host and port
            return True, msg[ack]
        # If the create slice request failed
        elif nack in msg:
            # Return the failure message
            return False, msg[nack]
        else:
            return False, "Missing ACK or NACK: " + str(msg)

    def create_slice(self, **kwargs):
        # Send Creation message
        success, msg = self._send_msg(self.create_ack, self.create_nack,
                                      **{self.create_msg: kwargs})

        # If the slice allocation failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed creating a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded creating a ' + self.type + ' Slice in ' + \
                  self.name)
            return True, msg

    def request_slice(self, **kwargs):
        # Send request message
        success, msg = self._send_msg(self.request_ack, self.request_nack,
                                      **{self.request_msg: kwargs})

        # If the slice request failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed requesting a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded requesting a ' + self.type + ' Slice in ' + self.name)
            return True, msg

        return msg

    def update_slice(self):
        # Send update message
        success, msg = self._send_msg(self.update_ack, self.update_nack,
                                      **{self.update_msg: kwargs})

        # If the slice update failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed updating a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded updating a ' + self.type + ' Slice in ' + \
                  self.name)
            return True, msg

        return msg

    def delete_slice(self, **kwargs):
        # Send removal message
        success, msg = self._send_msg(self.delete_ack, self.delete_nack,
                                      **{self.delete_msg: kwargs})

        # If the slice removal failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed deleting a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded deleting a ' + self.type + ' Slice in ' + \
                  self.name)
            return True, msg

        return msg


class hyperstrator_server(Thread):
    def __init__(self, **kwargs):
        # Initialize the parent class
        Thread.__init__(self)

        # Flat to exit gracefully
        self.shutdown_flag = Event()

        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Bind the server
        self._server_bind(**kwargs)

        # Container to hold the list of current services
        self.s_ids = []

        # Create an instance of the CN orchestrator handler
        self.cn_orch = orch_base(
            name="Core Network",
            host_key="cn_host",
            port_key="cn_port",
            default_host="127.0.0.1",
            default_port="2300",
            create_msg="cn_cc",
            request_msg="cn_rc",
            update_msg="cn_uc",
            delete_msg="cn_dc",
            request_key="cn_req",
            reply_key="cn_rep")

        # Create an instance of the TN orchestrator handler
        self.tn_orch = orch_base(
             name="Transport Network",
             host_key="tn_host",
             port_key="tn_port",
             default_host="127.0.0.1",
             default_port="2200",
             create_msg="tn_cc",
             request_msg="tn_rc",
             update_msg="tn_uc",
             delete_msg="tn_dc",
             request_key="tn_req",
             reply_key="tn_rep")

        # TODO Object there, but methods not implemented yet
        if False:
            # Create an instance of the TN orchestrator handler
            self.ran_orch = orch_base(
                 name="Radio Access Network",
                 host_key="ran_host",
                 port_key="ran_port",
                 default_host="127.0.0.1",
                 default_port="2300",
                 create_msg="tn_cc",
                 request_msg="rn_rc",
                 update_msg="rn_uc",
                 delete_msg="rn_dc",
                 request_key="rn_req",
                 reply_key="rn_rep")

    # Make printing easier. TODO: Implement real logging
    def _log(self, *args, head=False):
        print("-" if head else '\t' ,*args)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

        # Get the create service message from keyword arguments
        self.create_msg = kwargs.get('create_msg', 'sr_cs')
        # Get the create service acknowledgment from keyword arguments
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        # Get the request service message from keyword arguments
        self.request_msg = kwargs.get('request_msg', 'sr_rs')
        # Get the request service acknowledgment from keyword arguments
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        # Get the request service not acknowledgment from keyword arguments
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        # Get the update service message from keyword arguments
        self.update_msg = kwargs.get('update_msg', 'sr_us')
        # Get the update service acknowledgment from keyword arguments
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        # Get the update service not acknowledgment from keyword arguments
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        # Get the delete service message from keyword arguments
        self.delete_msg = kwargs.get('delete_msg', 'sr_ds')
        # Get the delete service acknowledgment from keyword arguments
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        # Get the delete service not acknowledgment from keyword arguments
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

        # Debug flags
        self.do_radio = kwargs.get('do_radio', True)
        self.do_transport= kwargs.get('do_transport', True)
        self.do_core = kwargs.get('do_core', True)

    # Bind server to socket
    def _server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '0.0.0.0')
        # Default HS Server port
        port = kwargs.get('port', 1000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, RECV_DELAY)

    def send_msg(self, message_type, message):
        # Send a message with a header
        self.socket.send_json({message_type: message})

    def run(self):
        self._log('Started Hyperstrator', head=True)
        # Run while thread is active
        while not self.shutdown_flag.is_set():

            try:
                # Wait for transaction
                transaction = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # Received a command
            else:
                # Start time counter
                st = time()
                # Service transaction , new service
                create_service = transaction.get(self.create_msg, None)

                # If the message worked
                if create_service is not None:
                    self._log('Create Service Transaction', head=True)
                    # Create a Service ID
                    s_id = str(uuid4())

                    self._log('Service ID:', s_id)

                    # If allocating CN slices
                    if self.do_core:
                        self._log('Send message to the CN orchestrator')
                        # Otherwise, send message to the CN orchestrator
                        core_success, core_msg = self.cn_orch.create_slice(
                            **{
                                's_id': s_id,
                                'requirements': create_service['requirements'],
                                'distribution': create_service['distribution']
                            })

                        # If the core allocation failed
                        if not core_success or 'source' not in core_msg:
                            self._log('Failed creating Core Slice')
                            # Inform the user about the failure
                            self.send_msg(
                                self.create_nack,
                                core_msg if not core_success else
                                "Malformatted message from CN orchestrator.")
                            # Measured elapsed time
                            self._log('Failed core, took:',
                                  (time() - st)*1000, 'ms')
                            # Finish the main loop here
                            continue

                        # Otherwise, the CN allocation succeeded
                        self._log('Succeeded creating a CN slice')

                    # In case of tests
                    else:
                        self._log('Skipping CN')
                        # Use a fake source IP
                        core_msg = {'s_id': s_id, 'source': '20.0.0.1'}


                    #TODO: RAN will come here
                    radio_msg = {'s_id': s_id, 'destination': '30.0.0.1'}


                    # If allocating TN slices
                    if self.do_transport:
                        self._log('Send message to the TN orchestrator')
                        # Send UUID and requirements to the TN orchestrator
                        transport_success, transport_msg = \
                            self.tn_orch.create_slice(
                            **{
                                's_id': s_id,
                                'requirements': create_service['requirements'],
                                'source': core_msg['source'],
                                'destination': radio_msg['destination']
                            })

                        # If the transport allocation failed
                        if not transport_success:
                            self._log('Failed creating Transport Slice')
                            # Inform the user about the failure
                            self.send_msg(
                                self.create_nack,
                                transport_msg if not transport_success else
                                "Malformatted message from TN orchestrator.")
                            # Measured elapsed time
                            self._log('Failed transport, took:',
                                  (time() - st)*1000, 'ms')
                            # Finish here
                            continue

                        # Otherwise, the transport allocation succeeded
                        self._log('Succeeded creating a TN Slice')

                    # In case of tests
                    else:
                        self._log('Skipping TN')
                        # Use a fake return message
                        transport_msg = {'s_id': s_id}

                    # Append it to the list of service IDs
                    self.s_ids.append(s_id)

                    # Inform the user about the configuration success
                    self.send_msg(self.create_ack, {
                        's_id': s_id
                    })

                    self._log('Creation time:', (time() - st)*1000, 'ms')

                # Service transaction, request service
                request_service = transaction.get(self.request_msg, None)

                # If the flag exists
                if request_service is not None:
                    self._log('Request Service Transaction', head=True)
                    # If missing the slice ID:
                    if request_service['s_id'] is None:
                        self._log("Missing Service ID.")
                        # Send message
                        self.send_msg(self.request_nack, "Missing Service ID")
                        # Leave if clause
                        continue

                    # If there is an S_ID but it doesn't exist
                    elif (request_service['s_id']) and \
                            (request_service['s_id'] not in self.s_ids):
                        self._log('Service ID does not exist')
                        # Send message
                        self.send_msg(self.request_nack,
                                      'The service does not exist: ' + \
                                      request_service['s_id'])
                        # Leave if clause
                        continue

                    # If gathering information about a slice
                    if request_service['s_id']:
                        self._log('Service ID:', request_service['s_id'])
                   # If set to gather information about all slices
                    else:
                        self._log('Gather information about all Service IDs')

                    # Container to hold information about the slices
                    slice_info = {s_id: {} for s_id in self.s_ids} \
                            if not request_service['s_id'] else \
                                    {request_service['s_id']: {}}

                    # If doing the CN
                    if self.do_core:
                        self._log('Send message to CN orchestrator')

                        # Otherwise, send message to the CN orchestrator
                        core_success, core_msg = self.cn_orch.request_slice(
                            **{'s_id': request_service['s_id']})

                        # If there was an error at the CN orchestrator
                        if not core_success:
                            self._log('Failed requesting Core Slice')
                            # Inform the user about the failure
                            self.send_msg(self.request_nack, core_msg)
                            # Finish here
                            continue

                        # Fill in the slice info
                        for s_id in slice_info:
                            slice_info[s_id]['cn'] = \
                                core_msg.get(s_id, "Not reported by CN")

                    # If debugging
                    else:
                        # Fill in the slice info with a stub
                        for s_id in slice_info:
                            slice_info[s_id]['cn'] = {'stub'}

                    # If doing the TN
                    if self.do_transport:
                        self._log('Send message to TN orchestrator')

                        # Otherwise, send message to the TN orchestrator
                        transport_success, transport_msg = \
                            self.tn_orch.request_slice(
                                **{'s_id': request_service['s_id']})

                        # If there was an error at the TN orchestrator
                        if not transport_success:
                            self._log('Failed requesting Transport Slice')
                            # Inform the user about the failure
                            self.send_msg(self.request_nack, transport_msg)
                            # Finish here
                            continue

                        # Fill in the slice info
                        for s_id in slice_info:
                            slice_info[s_id]['tn'] = \
                                transport_msg.get(s_id, "Not reported by TN")

                    # If debugging
                    else:
                        # Fill in the slice info with a stub
                        for s_id in slice_info:
                            slice_info[s_id]['tn'] = {'stub'}

                    # If doing the RAN
                    if self.do_radio:
                        self._log('Send message to RAN orchestrator')

                        # Otherwise, send message to the RAN orchestrator
                        radio_success, radio_msg = \
                            self.ran_orch.request_slice(
                                **{'s_id': request_service['s_id']})

                        # If there was an error at the RAN orchestrator
                        if not radio_success:
                            self._log('Failed requesting Radio Slice')
                            # Inform the user about the failure
                            self.send_msg(self.request_nack, radio_msg)
                            # Finish here
                            continue

                        # Fill in the slice info
                        for s_id in slice_info:
                            slice_info[s_id]['ran'] = \
                                radio_msg.get(s_id, "Not reported by RAN")

                    # If debugging
                    else:
                        # Fill in the slice info with a stub
                        for s_id in slice_info:
                            slice_info[s_id].update({'ran': 'stub'})



                    # Inform the user about the slice information
                    self.send_msg(self.request_ack, slice_info)
                    # Measure elapsed time
                    self._log('Get time:', (time() - st)*1000, 'ms')


                # Update service transaction
                update_service = transaction.get(self.update_msg, None)

                # If the flag exists
                if update_service is not None:
                    self._log('Update Service Transaction', head=True)

                    self._log("Not implemented yet.")

                    continue

                # Service transaction , remove service
                delete_service = transaction.get(self.delete_msg, None)

                # If the flag exists
                if delete_service is not None:
                    self._log('Delete Service Transaction', head=True)
                    # If missing the slice ID:
                    if delete_service['s_id'] is None:
                        self._log("Missing Service ID.")
                        # Send message
                        self.send_msg(self.delete_nack, "Missing Service ID")
                        # Leave if clause
                        continue

                    # If this service doesn't exist
                    elif delete_service['s_id'] not in self.s_ids:
                        self._log('Service ID does not exist')
                        # Send message
                        self.send_msg(self.delete_nack,
                                      'The service does not exist: ' + \
                                      delete_service['s_id'])
                        # Leave if clause
                        continue

                    self._log('Service ID:', delete_service['s_id'])

                    # If doing the CN
                    if self.do_core:
                        self._log('Send message to CN orchestrator')

                        # Otherwise, send message to the CN orchestrator
                        core_success, core_msg = self.cn_orch.delete_slice(
                            **{'s_id': delete_service['s_id']})

                        # If the core allocation failed
                        if not core_success:
                            self._log('Failed deleting Core Slice')
                            # Inform the user about the failure
                            self.send_msg(self.delete_nack, core_msg)
                            # Finish here
                            continue

                    # In case of testing
                    else:
                        self._log('Skipping core')

                    #TODO: The RAN will come here.

                    # If doing the TN
                    if self.do_transport:
                        self._log('Send message to the TN orchestrator')
                        # Otherwise, send message to the TN orchestrator
                        transport_success, transport_msg = \
                          self.tn_orch.delete_slice(
                            **{'s_id': delete_service['s_id']})

                        # If the TN allocation failed
                        if not tn_success:
                            self._log('Failed deleting Transport Slice')
                            # Inform the user about the failure
                            self.send_msg(self.delete_nack, transport_msg)
                            # Finish here
                            continue

                    # In case of testing
                    else:
                        self._log('Skipping TN')


                    # Remove it to the list of service IDs
                    self.s_ids.remove(delete_service['s_id'])

                    # Inform the user about the removal success
                    self.send_msg(self.delete_ack,
                                  {'s_id': delete_service['s_id']})

                # Check for unknown messages
                unknown_msg = [x for x in transaction  if x not in
                                [self.create_msg, self.request_msg,
                                 self.update_msg, self.delete_msg] ]
                # If there is at least an existing unknown message
                if unknown_msg:
                    self._log('Unknown message', head=True)
                    self._log('Message:', unknown_msg[0])

                    msg = {self.error_msg: "Unknown message:" + \
                           str(unknown_msg[0])}
                    # Send message
                    self.send_msg(self.error_msg, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()

    # Method for stopping the server thread nicely
    def safe_shutdown(self):
        print('Exiting')
        self.shutdown_flag.set()
        self.join()

if __name__ == "__main__":
    # Clear screen
    cls()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Hyperstrator Server
        hyperstrator_thread = hyperstrator_server(
            host='127.0.0.1',
            port=1100,
            error_msg='msg_err',
            create_msg='sr_cs',
            request_msg='sr_rs',
            update_msg='sr_us',
            delete_msg='sr_ds',
            do_radio=False,
            do_transport=False,
            do_core=True)
        # Start the Hyperstrator Thread
        hyperstrator_thread.start()
        # Pause the main thread
        pause()

    except KeyboardInterrupt:
        # Terminate the Hyperstrator
        hyperstrator_thread.safe_shutdown()
