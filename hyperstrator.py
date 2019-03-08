#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the uuid4 function from the UUID module
from uuid import uuid4
# Import the system method from the OS module
from os import system, name
# Import the Pause method from the Signal module
from signal import pause

# Clear terminal screen
def cls():
    # Perform action based on the current platform
    system('cls' if name=='nt' else 'clear')


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

        self.request_msg = kwargs.get("request_msg", "bo_rrs" )
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        self.update_msg = kwargs.get("update_msg", "bo_urs")
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        self.delete_msg = kwargs.get("delete_msg", "bo_drs" )
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
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
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
        success, msg = self._send_msg(
            self.create_ack, self.create_nack, **{self.create_msg: kwargs})

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
        success, msg = self._send_msg(
            self.request_ack, self.request_nack, **{self.request_msg: kwargs})

        # If the slice request failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed requesting a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded requesting a ' + self.type + \
                  ' Slice in ' + self.name)
            return True, msg

        return msg

    def update_slice(self):
        # Send update message
        success, msg = self._send_msg(
            self.update_ack, self.update_nack, **{self.update_msg: kwargs})

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
        success, msg = self._send_msg(
            self.delete_ack, self.delete_nack, **{self.delete_msg: kwargs})

        # If the slice removal failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed removing a ' + self.type + ' Slice in ' + \
                  self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded removing a ' + self.type + ' Slice in ' + \
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

        # Create an instance of the SDN orchestrator handler
        self.sdn_orch = orch_base(name="Wired Network",
                                  host_key="sdn_host",
                                  port_key="sdn_port",
                                  default_host="127.0.0.1",
                                  default_port="2200",
                                  create_msg="wd_cc",
                                  request_msg="wd_rc",
                                  update_msg="wd_uc",
                                  delete_msg="wd_dc",
                                  request_key="sdn_req",
                                  reply_key="sdn_rep")

        # Create an instance of the SDR orchestrator handler
        self.sdr_orch = orch_base(name="Wireless Network",
                                  host_key="sdr_host",
                                  port_key="sdr_port",
                                  default_host="127.0.0.1",
                                  default_port="2100",
                                  create_msg="wl_cr",
                                  request_msg="wl_rr",
                                  update_msg="wl_ur",
                                  delete_msg="wl_dr",
                                  request_key="sdr_req",
                                  reply_key="sdr_rep")


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
         # Get the create service acknowledgment from keyword arguments
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        # Get the remove service message from keyword arguments
        self.update_msg = kwargs.get('update_msg', 'sr_us')
         # Get the create service acknowledgment from keyword arguments
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        # Get the remove service message from keyword arguments
        self.delete_msg = kwargs.get('delete_msg', 'sr_ds')
         # Get the create service acknowledgment from keyword arguments
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

    # Bind server to socket
    def _server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default HS Server port
        port = kwargs.get('port', 1000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)

    def send_msg(self, message_type, message):
        # Send a message with a header
        self.socket.send_json({message_type: message})

    def run(self):
        print('- Started Hyperstrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

             try:
                # Wait for request
                request = self.socket.recv_json()
             # If nothing was received during the timeout
             except zmq.Again:
                # Try again
                continue

             # Received a command
             else:
                # Service request, new service
                create_service = request.get(self.create_msg, None)

                # If the message worked
                if create_service is not None:
                    print('- Create Service Request')
                    # Create a Service ID
                    s_id = str(uuid4())

                    print('\t', 'Service ID:', s_id)
                    print('\t', 'Send message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    radio_success, radio_msg = self.sdr_orch.create_slice(
                        **{'type': create_service['type'], 's_id': s_id})

                    # If the radio allocation failed
                    if not radio_success:
                        print('\t', 'Failed creating Radio Slice')
                        # Inform the user about the failure
                        self.send_msg(self.create_nack, radio_msg)
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\t', 'Succeeded creating a Radio Service')

                    # Otherwise, send message to the SDN orchestrator
                    core_success, core_msg = self.sdn_orch.create_slice(
                        **{'type': create_service['type'],
                            's_id': s_id,
                            'destination': radio_msg['host'],
                            'source': '127.0.0.1'})

                    # If the core allocation failed
                    if not core_success:
                        print('\t', 'Failed creating Core Slice')
                        # Inform the user about the failure
                        self.send_msg(self.create_nack, core_msg)
                        # Finish here
                        continue

                    # Append it to the list of service IDs
                    self.s_ids.append(s_id)

                    # Inform the user about the configuration success
                    # TODO the host and port should come from the SDN orch.
                    self.send_msg(self.create_ack, {'s_id': s_id,
                                                    'host': radio_msg['host']})

                # Service rerquest, remove service
                delete_service = request.get(self.delete_msg, None)

                 # If the flag exists
                if delete_service is not None:
                    print('- Delete Service Request')
                    # If this service doesn't exist
                    if delete_service['s_id'] not in self.s_ids:
                        print('\t', 'Service ID does not exist')
                        # Send message
                        self.send_msg(self.delete_nack,
                                      'The service does not exist: ' + \
                                      delete_service['s_id'])

                        # Leave if clause
                        continue

                    print('\t', 'Service ID:', delete_service['s_id'])
                    print('\t', 'Send message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    radio_success, radio_msg = self.sdr_orch.delete_slice(
                        **{'s_id': delete_service['s_id']})

                    # If the radio removal failed
                    if not radio_success:
                        # Inform the user about the failure
                        self.send_msg(self.delete_nack, radio_msg,)
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\t', 'Succeeded removing a Radio Service')

                    # Otherwise, send message to the SDN orchestrator
                    core_success, core_msg = self.sdn_orch.delete_slice(
                        **{'s_id': delete_service['s_id']})

                    # If the core allocation failed
                    if not core_success:
                        print('\t', 'Failed removing Core Slice')
                        # Inform the user about the failure
                        self.send_msg(self.delete_nack, core_msg)
                        # Finish here
                        continue

                    # Remove it to the list of service IDs
                    self.s_ids.remove(delete_service['s_id'])

                    # Inform the user about the removal success
                    self.send_msg(self.delete_ack,
                                  {'s_id': delete_service['s_id']})

                # Check for unknown messages
                unknown_msg = [x for x in request if x not in [self.create_msg,
                                                               self.request_msg,
                                                               self.update_msg,
                                                               self.delete_msg]]
                # If there is at least an existing unknown message
                if unknown_msg:
                    print('- Unknown message')
                    print('\t', 'Message:', unknown_msg[0])

                    msg = {self.error_msg: "Unknown message:" + \
                           str(unknown_msg[0])}
                    # Send message
                    self.send_msg(self.error_msg, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()


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
            remove_msg='sr_rs',
            create_radio='wl_cr',
            remove_radio='wl_dr',
            create_core='wd_cc',
            remove_core='wd_rc',
        )
        # Start the Hyperstrator Thread
        hyperstrator_thread.start()
        # Pause the main thread
        pause()

    except KeyboardInterrupt:
        # Terminate the Hyperstrator
        hyperstrator_thread.shutdown_flag.set()
        hyperstrator_thread.join()
        print('Exiting')
