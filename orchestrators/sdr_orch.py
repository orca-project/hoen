#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
# Import the System and Name methods from the OS module
from os import system, name

import signal

def cls():
    system('cls' if name=='nt' else 'clear')


class ctl_base(object):

    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        self.name = kwargs.get('name', '')
        self.type = kwargs.get('type', '')
        self.host_key = kwargs.get("host_key", "")
        self.port_key = kwargs.get("port_key", "")
        self.default_host = kwargs.get("default_host", "127.0.0.1")
        self.default_port = kwargs.get("default_port", "1600")
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

        self.create_msg = kwargs.get("create_msg", "wlc_crs")
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        self.request_msg = kwargs.get("request_msg", "wlc_rrs" )
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        self.update_msg = kwargs.get("update_msg", "wlc_urs")
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        self.delete_msg = kwargs.get("delete_msg", "wlc_drs" )
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

    def _server_connect(self, **kwargs):
        # Default Server host
        host = kwargs.get(self.host_key, self.default_host)
        # Default Server port
        port = kwargs.get(self.port_key, self.default_port)
        # Create a ZMQ context

        self.context = zmq.Context()
        #  Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REQ)
        # Connect ZMQ socket to host:port
        self.socket.connect("tcp://" + host + ":" + str(port))
        # Timeout reception every 5 seconds
        self.socket.setsockopt(zmq.RCVTIMEO, 3000)
        # # Allow multiple requests and replies
        self.socket.setsockopt(zmq.REQ_RELAXED, 1)
        # # Add IDs to ZMQ messages
        self.socket.setsockopt(zmq.REQ_CORRELATE, 1)


    def _send_msg(self, **kwargs):
        # Send message the hyperstrator
        self.socket.send_json({self.request_key: kwargs})

        try:
            # Wait for command
            msg = self.socket.recv_json().get(self.reply_key, None)
        # If nothing was received during the timeout
        except zmq.Again:
            # Try again
            return None, "Connection timeout to " + self.name + " Controller"


        # If the message is not valid
        if msg is None:
            # Return proper error
            return None, "Received invalid message: " + str(msg)
        # The orchestrator couldn't decode message
        elif self.error_msg in msg:
            return None, msg[self.error_msg]
        # If failed creating a slice
        elif self.create_nack in msg:
            # Return the failure message
            return None, msg[self.create_nack]
        # If succeeded creating a slice
        elif self.create_ack in msg:
            # Return host and port
            return msg[self.create_ack]['host'], \
                msg[self.create_ack]['port']
        # If succeeded removing a slice
        elif self.delete_ack in msg:
            # Return the Service ID  to confirm it
            return msg[self.delete_ack], None
        # If failed removing a slice
        elif self.delete_nack in msg:
            # Return the error message
            return None, msg[self.delete_nack]
        # Unexpected behavior
        else:
            return None, "Missing ACK or NACK: " + str(msg)


    def create_slice(self, s_id, s_type):
        # Send creation message
        host, port = self._send_msg(**{self.create_msg: {'type': s_type,
                                                         's_id': s_id}})

        # If the slice allocation failed
        if host is None:
            # Inform the hyperstrator about the failure
            print('\tFailed creating a ' + self.type + ' Slice in ' + self.name)
            msg = {self.create_nack: {'msg': port}}

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\tSucceeded creating a ' + self.type + ' Slice in ' + self.name)
            msg = {self.create_ack: {'host': host, 'port': port}}

        return msg

    def request_slice(self):
        # TODO Implement method
        pass

    def update_slice(self):
        # TODO implement method
        pass

    def delete_slice(self, s_id, s_type):
        # Send removal message
        host, port = self._send_msg(**{self.delete_msg: {'type': s_type,
                                                         's_id': s_id}})

        # If the slice removal failed
        if host is None:
            # Inform the hyperstrator about the failure
            print('\tFailed removing a ' + self.type + ' Slice in ' + self.name)
            msg = {self.delete_nack: {'msg': port}}

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\tSucceeded removing a ' + self.type + ' Slice in ' + self.name)
            msg = {self.delete_ack: {'s_id': host}}

        return msg

class wireless_orchestrator_server(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # COntainer to hold the list of Service IDs
        self.s_ids = {}


        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Start the HS server
        self._server_bind(**kwargs)

        # IMEC Controller Handler
        self.imec_ctl = ctl_base(
            name="IMEC",
            host_key="imec_host",
            port_key="imec_port",
            default_host="1127.0.0.1",
            default_port="3100",
            request_key="imec_req",
            reply_key="imec_rep")

        # TCD Controller Handler
        self.tcd_ctl = ctl_base(
            name="TCD",
            host_key="tcd_host",
            port_key="tcd_port",
            default_host="127.0.0.1",
            default_port="3200",
            request_key="tcd_req",
            reply_key="tcd_rep")

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')

        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'sdr_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'sdr_rep')

        # Get the create service message from keyword arguments
        self.create_msg = kwargs.get('create_msg', 'wl_cr')
         # Get the create service acknowledgment from keyword arguments
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        # Get the request service message from keyword arguments
        self.request_msg = kwargs.get('request_msg', 'wl_rr')
         # Get the create service acknowledgment from keyword arguments
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        self.update_msg = kwargs.get('update_msg', 'wl_ur')
         # Get the create service acknowledgment from keyword arguments
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        self.delete_msg = kwargs.get('delete_msg', 'wl_dr')
         # Get the create service acknowledgment from keyword arguments
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        # Get the create service not acknowledgment from keyword arguments
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])


    def _server_bind(self, **kwargs):
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
        # Timeout reception every 500 milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, 500)


    def send_msg(self, message_header, message):
        # Send a message with a header
        self.socket.send_json({message_header: message})


    def run(self):
        print('- Started Wireless Orchestrator')
        # Run while thread is active
        while not self.shutdown_flag.is_set():

            # Wait for command
            try:
                cmd = self.socket.recv_json()

            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # Request
            request = cmd.get(self.req_header, None)

            # If the message is valid
            if request is not None:
                print('- Received Message')
                # Check whether is it a new service
                create_slice = request.get(self.create_msg, None)

                # If it is a new service
                if create_slice is not None:
                    print('- Create Radio Service')
                    # This service already exists
                    if create_slice['s_id'] in self.s_ids:
                        print('\tService ID already exists.')
                        msg = {self.create_nack:
                               'The service already exists: ' + \
                               create_slice['s_id']}
                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue
                    # Otherwise, it is a new service
                    # Append it to the list of service IDs
                    self.s_ids[create_slice['s_id']] = create_slice.get('type',
                                                                        None)

                    print('\tService ID:', create_slice['s_id'])

                    # Decide what to do based on the type of traffic
                    if create_slice['type'] == "high-throughput":
                        # Send message to TCD SDR controller
                        print('\tTraffic type: High Throughput')
                        print('\tDelegating it to the TCD Controller')

                        # Send the message to create a slice
                        msg = self.tcd_ctl.create_slice(
                            create_slice['s_id'], create_slice['type'])

                    elif create_slice['type'] == "low-latency":
                        # Send messate to IMEC SDR Controller
                        print('\tTraffic type: Low Latency')
                        print('\tDelegating it to the IMEC Controller')

                        # Send the message to create a slice
                        msg = self.imec_ctl.create_slice(
                            create_slice['s_id'], create_slice['type'])

                    # Otherwise, couldn't identify the traffic type
                    else:
                        print('\tInvalid traffic type.')
                        # Send NACK
                        msg = {self.create_nack:
                               'Could not identify the traffic type:' +
                              str(create_slice['type'])}

                        # Remove the service from the list of service IDs
                        del self.s_ids[create_slice['s_id']]

                    # Send message
                    self.send_msg(self.rep_header, msg)

                # If it is a remove service
                delete_slice = request.get(self.delete_msg, None)

                if delete_slice is not None:
                    print('- Remove Radio Service')
                    # If this service doesn't exist
                    if delete_slice['s_id'] not in self.s_ids:
                        print('\tService ID doesn\' exist')
                        msg = {'ds_nack': 'The service doesn\' exist:' +
                               delete_slice['s_id']}

                        # Send message
                        self.send_msg(self.rep_header, msg)
                        # Leave if clause
                        continue

                    # Decide what to do based on the type of traffic
                    if self.s_ids[delete_slice['s_id']] == "high-throughput":
                        # Send message to TCD SDR controller
                        print('\tTraffic type: High Throughput')
                        print('\tDelegating it to the TCD Controller')

                        # Send message to remove slice
                        msg = self.tcd_ctl.remove_slice(
                            delete_slice['s_id'],
                            self.s_ids[delete_slice['s_id']])

                    elif self.s_ids[delete_slice['s_id']] == "low-latency":
                        # Send messate to IMEC SDR Controller
                        print('\tTraffic type: Low Latency')
                        print('\tDelegating it to the IMEC Controller')

                        # Send message to remove slice
                        msg = self.imec_ctl.remove_slice(
                            delete_slice['s_id'],
                            self.s_ids[delete_slice['s_id']])

                    # Remove the service from the list of service IDs
                    del self.s_ids[delete_slice['s_id']]
                    # Send message
                    self.send_msg(self.rep_header, msg)


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
                    self.send_msg(self.rep_header, msg)

            # Failed to parse message
            else:
                print('- Failed to parse message')
                print('\t', 'Message:', cmd)

                msg = {self.error_msg: "Failed to parse message:" + str(cmd)}
                # Send message
                self.send_msg(self.rep_header, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        wireless_orchestrator_thread = wireless_orchestrator_server(
            host='127.0.0.1', port=2100)
        wireless_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wireless Orchestrator Server
        print('Exiting')
        wireless_orchestrator_thread.shutdown_flag.set()
        wireless_orchestrator_thread.join()
