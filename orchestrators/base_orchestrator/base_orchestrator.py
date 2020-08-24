#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the Time and Sleep methods from the time module
from time import time, sleep
# Import the System and Name methods from the OS module
from os import system, name
# Import the format exception method from the traceback module
from traceback import format_exc

# Received delay of 10 sec
RECV_DELAY = 60*1000

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

        # parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Connect to the server
        self._server_connect(**kwargs)

    # Make printing easier. TODO: Implement real logging
    def _log(self, *args, head=False):
        print("-" if head else '\t' ,*args)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get("error_msg", "msg_err")

        self.info_msg = kwargs.get("info_msg", "ctl_ni")
        self.info_ack = "_".join([self.info_msg.split('_')[-1], "ack"])
        self.info_nack = "_".join([self.info_msg.split('_')[-1], "nack"])

        self.create_msg = kwargs.get("create_msg", "ctl_cs")
        self.create_ack = "_".join([self.create_msg.split('_')[-1], "ack"])
        self.create_nack = "_".join([self.create_msg.split('_')[-1], "nack"])

        self.request_msg = kwargs.get("request_msg", "ctl_rs" )
        self.request_ack = "_".join([self.request_msg.split('_')[-1], "ack"])
        self.request_nack = "_".join([self.request_msg.split('_')[-1], "nack"])

        self.update_msg = kwargs.get("update_msg", "ctl_us")
        self.update_ack = "_".join([self.update_msg.split('_')[-1], "ack"])
        self.update_nack = "_".join([self.update_msg.split('_')[-1], "nack"])

        self.delete_msg = kwargs.get("delete_msg", "ctl_ds" )
        self.delete_ack = "_".join([self.delete_msg.split('_')[-1], "ack"])
        self.delete_nack = "_".join([self.delete_msg.split('_')[-1], "nack"])

        self.topology_msg = kwargs.get("topology_msg", "ctl_ts")
        self.topology_ack = "_".join([self.topology_msg.split('_')[-1], "ack"])
        self.topology_nack = "_".join([self.topology_msg.split('_')[-1], "nack"])

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


    def network_info(self, **kwargs):
        # Send Info message
        success, msg = self._send_msg(self.info_ack, self.info_nack,
                                      **{self.info_msg: kwargs})

        # If the message failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed requesting information about the ' + self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded requesting information about the ' + \
                  self.name)
            return True, msg

    def create_slice(self, **kwargs):
        # Send Creation message
        success, msg = self._send_msg(
            self.create_ack, self.create_nack, **{self.create_msg: kwargs})

        # If the slice allocation failed
        if not success:
            # Inform the hyperstrator about the failure
            print('\t', 'Failed creating a ' + self.type + ' Slice in ' + \
                    self.name, "Reason:", msg)
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
                  self.name, "Reason:", msg)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded requesting a ' + self.type + ' Slice in ' + self.name)
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
                  self.name, "Reason:", msg)
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
            print('\t', 'Failed deleting a ' + self.type + ' Slice in ' + \
                  self.name, "Reason:", msg)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            print('\t', 'Succeeded deleting a ' + self.type + ' Slice in ' + \
                  self.name)
            return True, msg

        return msg

    def get_topology(self, **kwargs):
        # Send request message
        success, msg = self._send_msg(
            self.topology_ack, self.topology_nack, **{self.topology_msg: kwargs})

        # If the slice request failed
        if not success:
            # Inform the hyperstrator about the failure
            self._log('Failed requesting a ' + self.type + \
                      ' topology in ' + self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            self._log('Succeeded requesting a ' + self.type + \
                      ' topology in ' + self.name)
            return True, msg

        return msg

class base_orchestrator(Thread):

    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # Container to hold the list of Service IDs
        self.s_ids = {}

        # Parse keyword arguments
        self._parse_kwargs(**kwargs)
        # Start the HS server
        self._server_bind(**kwargs)

        # Run post initialization operations
        self.post_init(**kwargs)

    # Make printing easier. TODO: Implement real logging
    def _log(self, *args, head=False):
        print("-" if head else '\t' ,*args)

    # Extract message headers from keyword arguments
    def _parse_kwargs(self, **kwargs):
        # Get the error message header from keyword arguments
        self.error_msg = kwargs.get('error_msg', 'msg_err')
        self.name = kwargs.get('name', '')
        self.type = kwargs.get('type', '')

        # Get the request header from keyword arguments
        self.req_header = kwargs.get('req_header', 'sdr_req')
        # Get the reply header from keyword arguments
        self.rep_header = kwargs.get('rep_header', 'sdr_rep')

        # Get the network info message from keyword arguments
        self.info_msg = kwargs.get('info_msg', 'ns_ri')
        # Get the network info acknowledgment from keyword arguments
        self.info_ack = "_".join([self.info_msg.split('_')[-1], "ack"])
        # Get the network info not acknowledgment from keyword arguments
        self.info_nack = "_".join([self.info_msg.split('_')[-1], "nack"])

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
        host = kwargs.get('host', '0.0.0.0')
        # Default HS Server port
        port = kwargs.get('port', 4000)

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


    def run(self):
        self._log('Started ' + self.name + ' Orchestrator', head=True)
        # Run while thread is active
        while not self.shutdown_flag.is_set():
            # Wait for command
            try:
                cmd = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                # Try again
                continue

            # Start time counter
            st = time()

            # Received transaction
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

                # Check whether is it a new service
                create_slice = transaction.get(self.create_msg, None)

                # If it is a new service
                if create_slice is not None:
                    self._log('Create ' + self.type + ' Service', head=True)
                    # This service already exists
                    if create_slice['s_id'] in self.s_ids:
                        self._log('Service ID already exists.')
                        msg = 'The service already exists: ' + \
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

                    # In care of issues for creating slice
                    if not success:
                        self.s_ids.pop(create_slice['s_id'], None)

                    # In case of issues to create slice
                    if not success:
                        del self.s_ids[create_slice['s_id']]

                    # Log event
                    self._log("Created Slice" if success else \
                        "Failed creating Slice", 'Took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.create_ack if success else \
                                   self.create_nack, msg)


                # If it is a request service
                request_slice = transaction.get(self.request_msg, None)

                if request_slice is not None:
                    self._log('Request' + self.type + ' Service', head=True)
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
                        self._log('The service does not exist')
                        # Send message
                        self.send_msg(self.request_nack,
                                      'The service does not exist: ' + \
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
                        "Failed requesting  slice", 'took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.request_ack if success else \
                                   self.request_nack, msg)

                # Update service transaction
                update_slice = transaction.get(self.update_msg, None)

                # If the flag exists
                if update_slice is not None:
                    self._log('Update Service Transaction', head=True)

                    self._log("Not implemented yet.")

                    continue

                # If it is a delete service
                delete_slice = transaction.get(self.delete_msg, None)

                if delete_slice is not None:
                    self._log('Delete' + self.type + ' Service', head=True)
                    # If missing the slice ID:
                    if delete_slice['s_id'] is None:
                        self._log("Missing Service ID.")
                        # Send message
                        self._send_msg(self.delete_nack, "Missing Service ID")
                        # Leave if clause
                        continue

                    # If this service doesn't exist
                    elif delete_slice['s_id'] not in self.s_ids:
                        self._log('Service ID does not exist')
                        msg = 'The service does not exist:' + \
                            delete_slice['s_id']
                        # Send message
                        self._send_msg(self.delete_nack, msg)
                        # Leave if clause
                        continue

                    self._log('Service ID:', delete_slice['s_id'])

                    try:
                        # Delete a slice
                        success, msg = self.delete_slice(**delete_slice)
                    except Exception:
                        success = False
                        msg = str(format_exc())

                    # Log event
                    self._log("Deleted Slice" if success else \
                        "Failed deleting  slice", 'took:',
                              (time() - st)*1000, 'ms')

                    # Send message
                    self._send_msg(self.delete_ack if success else \
                                   self.delete_nack, msg)

                    # Delete it from the list of service IDs
                    del self.s_ids[delete_slice['s_id']]


                # Check for unknown messages
                unknown_msg = [x for x in transaction if x not in [
                    self.create_msg, self.request_msg,
                    self.update_msg, self.delete_msg,
                    self.info_msg]]

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
                self._log('Message:', cmd)

                msg = "Failed to parse message: " + str(cmd)
                # Send message
                self._send_msg(self.error_msg, msg)

        # Terminate zmq
        self.socket.close()
        self.context.term()

    # Method for stopping the server thread nicely
    def safe_shutdown(self):
        self._log("Exiting", head=True)
        self.shutdown_flag.set()
        self.join()


if __name__ == "__main__":
    # clear screen
    cls()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Template Orchestrator
        template_orchestrator_thread = base_orchestrator(
            name='ORC',
            type='Generic',
            req_header='orc_req',
            rep_header='orc_rep',
            error_msg='msg_err',
            info_msg='oc_ni',
            create_msg='oc_cs',
            request_msg='oc_rs',
            update_msg='oc_us',
            delete_msg='oc_ds',
            host='0.0.0.0',
            port=2000)

        # Start the Template Orchestrator Thread
        template_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Template Orchestrator Server
        template_orchestrator_thread.safe_shutdown()
