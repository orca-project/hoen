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
    host_key = ""
    port_key = ""
    default_host = "127.0.0.1"
    default_port = "3000"
    request_key = ""
    reply_key = ""

    def __init__(self, **kwargs):
         # Connect to the server
        self.server_connect(**kwargs)


    def server_connect(self, **kwargs):
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


    def send_msg(self, kwargs):
        # Send request to the orchestrator
        self.socket.send_json({self.request_key: kwargs})
        # Wait for command
        msg = self.socket.recv_json().get(self.reply_key, None)
        # If the message is not valid
        if msg is None:
            # Return proper error
            return None, "Received invalid message: " + str(msg)
        # The orchestrator couldn't decode message
        elif 'msg_err' in msg:
            return None, msd['msg_err']
        # If the create slice request succeeded
        elif 'ns_ack' in msg:
            # Return host and port
            return msg['ns_ack']['host'], msg['ns_ack']['port']
        # If the create slice request failed
        elif 'ns_nack' in msg:
            # Return the failure message
            return None, msg['ns_nack']
        # If the remove slice request succeeded
        elif 'rs_ack' in msg:
            # Return the Service ID to confirm it
            return msg['rs_ack'], None
         # If the remove slice request failed
        elif 'rs_nack' in msg:
            # Return the failure message
            return None, msg['rs_nack']
        # Unexpected behaviour
        else:
            return None, "Missing ACK or NACK: " + str(msg)


class sdn_orch(orch_base):
    host_key = "sdn_host"
    port_key = "sdn_port"
    default_host = "127.0.0.1"
    default_port = "5000"
    request_key = "sdn_req"
    reply_key = "sdn_rep"

# TODO put the orchestrators inside the hyperstrator class
class sdr_orch(orch_base):
    host_key = "sdr_host"
    port_key = "sdr_port"
    default_host = "127.0.0.1"
    default_port = "2000"
    request_key = "sdr_req"
    reply_key = "sdr_rep"


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
        self.sdn_orch = sdn_orch()
        # Create an instance of the SDR orchestrator handler
        self.sdr_orch = sdr_orch()

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

         # Get the create service message from keyword arguments
        self.create_msg = kwargs.get('create_msg', 'sr_cs')
         # Get the create service acknowledgment from keyword arguments
        self.create_ack = kwargs.get('create_ack', 'cs_ack')
        # Get the create service not acknowledgment from keyword arguments
        self.create_nack = kwargs.get('create_nack', 'cs_nack')

        # Get the request service message from keyword arguments
        self.request_msg = kwargs.get('request_msg', 'sr_rs')
         # Get the create service acknowledgment from keyword arguments
        self.request_ack = kwargs.get('request_ack', 'rs_ack')
        # Get the create service not acknowledgment from keyword arguments
        self.request_nack = kwargs.get('request_nack', 'rs_nack')

        # Get the remove service message from keyword arguments
        self.update_msg = kwargs.get('update_msg', 'sr_us')
         # Get the create service acknowledgment from keyword arguments
        self.update_ack = kwargs.get('update_ack', 'us_ack')
        # Get the create service not acknowledgment from keyword arguments
        self.update_nack = kwargs.get('update_nack', 'us_nack')

        # Get the remove service message from keyword arguments
        self.delete_msg = kwargs.get('delete_msg', 'sr_ds')
         # Get the create service acknowledgment from keyword arguments
        self.delete_ack = kwargs.get('delete_ack', 'ds_ack')
        # Get the create service not acknowledgment from keyword arguments
        self.delete_nack = kwargs.get('delete_nack', 'ds_nack')

        # Get the create radio slice message from keyword arguments
        self.create_radio = kwargs.get('create_radio', 'r_cs')
        # Get the request radio slice message from keyword arguments
        self.request_radio = kwargs.get('request_radio', 'r_rs')
        # Get the update radio slice message from keyword arguments
        self.update_radio = kwargs.get('update_radio', 'r_us')
        # Get the remove radio slice message from keyword arguments
        self.remove_radio = kwargs.get('delete_radio', 'r_ds')

        # Get the create core slice message from keyword arguments
        self.create_core = kwargs.get('create_core', 'c_cs')
        # Get the request core slice message from keyword arguments
        self.request_core = kwargs.get('request_core', 'c_rs')
        # Get the update core slice message from keyword arguments
        self.update_core = kwargs.get('update_core', 'c_us')
        # Get the remove core slice message from keyword arguments
        self.remove_remove = kwargs.get('delete_msg', 'c_ds')

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


    def run(self):
        print('- Started Hyperstrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

             try:
                # Wait for command
                cmd = self.socket.recv_json()
             # If nothing was received during the timeout
             except zmq.Again:
                # Try again
                continue

             # Received a command
             else:
                # Service request, new service
                create_service = cmd.get(self.create_msg, None)

                # If the message worked
                if create_service is not None:
                    print('- Create Service Request')
                    # Create a Service ID
                    s_id = str(uuid4())

                    print('\tService ID:', s_id)
                    print('\tSend message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    r_host, r_port = self.sdr_orch.send_msg(
                        {self.create_radio: {'type': create_service['type'],
                                             's_id': s_id}})

                    # If the radio allocation failed
                    if r_host is None:
                        print('\tFailed creating Radio Slice')
                        # Inform the user about the failure
                        self.socket.send_json({self.create_nack: r_port})
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\tSucceeded creating a Radio Service')

                    # TODO For the future, SDN hooks
                    if False:
                        # Otherwise, send message to the SDN orchestrator
                        c_host, c_port = self.sdn_orch.send_msg(
                            {self.create_core: {
                                'type': create_service['type'],
                                's_id': s_id,
                                'destination': (r_host, r_port),
                                'source': ('127.0.0.1', 6000)
                            }})

                    # TODO if the wired and the wireless parts worked
                    # Append it to the list of service IDs
                    self.s_ids.append(s_id)

                    # Inform the user about the configuration success
                    # TODO the host and port should come from the SDN orch.
                    self.socket.send_json({self.create_ack: {'s_id': s_id,
                                                             'host': r_host,
                                                             "port": r_port}})

                # Service rerquest, remove service
                remove_service = cmd.get(self.remove_msg, None)

                 # If the flag exists
                if remove_service is not None:
                    print('- Remove Service Request')
                    # If this service doesn't exist
                    if remove_service['s_id'] not in self.s_ids:
                        print('\tService ID doesn\' exist')
                        # Send message
                        self.socket.send_json(
                            {self.remove_nack: 'The service doesn\'t exist:' +
                             remove_service['s_id']})

                        # Leave if clause
                        continue

                    print('\tService ID:', remove_service['s_id'])
                    print('\tSend message to SDR orchestrator')
                    # Send UUID and type of service to the SDR orchestrator
                    r_host, r_port = self.sdr_orch.send_msg(
                        {self.remove_radio: {'s_id': remove_service['s_id']}})

                    # If the radio removal failed
                    if r_host is None:
                        # Inform the user about the failure
                        self.socket.send_json({self.remove_nack: r_port})
                        # Finish here
                        continue

                    # Otherwise, the radio allocation succeeded
                    print('\tSucceeded removing a Radio Service')

                    # TODO For the future, SDN hooks
                    if False:
                        # Otherwise, send message to the SDN orchestrator
                        c_host, c_port = self.sdn_orch.send_msg(
                            {self.remove_core: {'s_id': remove_slice['s_id']}})

                    # TODO if the wired and the wireless parts worked
                    # Remove it to the list of service IDs
                    self.s_ids.remove(remove_service['s_id'])

                    # Inform the user about the removal success
                    self.socket.send_json(
                        {self.remove_ack: {'s_id': remove_service['s_id']}})

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
            host='192.168.0.100',
            port=1000,
            error_msg='msg_err',
            create_msg='sr_cs',
            create_ack='cs_ack',
            create_nack='cs_nack',
            remove_msg='sr_rs',
            remove_ack='rs_ack',
            remove_nack='rs_nack',
            create_radio='r_rs',
            remove_radio='r_rr',
            create_core='c_rs',
            remove_core='c_rr',
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
