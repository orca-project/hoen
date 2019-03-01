#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Orchestrator
from base_orchestrator.base_orchestrator import base_orchestrator, ctl_base
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal

def cls():
    system('cls' if name=='nt' else 'clear')

class wireless_orchestrator_server(base_orchestrator):

    def post_init(self, **kwargs):
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

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        s_type = kwargs.get('s_type', None)

        # Append it to the list of service IDs
        self.s_ids[s_id] = s_type

        print('\t', 'Service ID:', s_id)

        # Decide what to do based on the type of traffic
        if s_type == "high-throughput":
            # Send message to TCD SDR controller
            print('\t', 'Traffic type: High Throughput')
            print('\t', 'Delegating it to the TCD Controller')

            # Send the message to create a slice
            success, msg = self.tcd_ctl.create_slice(
                **{'s_id': s_id,'type': s_type})

            # Inform the user about the creation
            return success, msg


        elif create_slice['type'] == "low-latency":
            # Send messate to IMEC SDR Controller
            print('\t', 'Traffic type: Low Latency')
            print('\t', 'Delegating it to the IMEC Controller')

            # Send the message to create a slice
            success, msg = self.imec_ctl.create_slice(
                **{'s_id': s_id, 's_type': s_type})

            # Inform the user about the creation
            return success, msg

        # Otherwise, couldn't identify the traffic type
        else:
            print('\t', 'Invalid traffic type.')

            # Remove the service from the list of service IDs
            del self.s_ids[s_id]

            # Send error message
            msg = 'Could not identify the traffic type:' + str(s_type)
            # Inform the user about the creation
            return success, msg


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        print('\t', 'Service ID:', s_id)

        # Decide what to do based on the type of traffic
        if self.s_ids[s_id] == "high-throughput":
            # Send message to TCD SDR controller
            print('\t', 'Traffic type: High Throughput')
            print('\t', 'Delegating it to the TCD Controller')

            # Send message to remove slice
            success, msg = self.tcd_ctl.delete_slice(
                **{'s_id': s_id,  'type': self.s_ids[s_id]})

            # Inform the user about the removal
            return success, msg


        elif self.s_ids[s_id] == "low-latency":
            # Send messate to IMEC SDR Controller
            print('\t', 'Traffic type: Low Latency')
            print('\t', 'Delegating it to the IMEC Controller')

            # Send message to remove slice
            success, msg = self.imec_ctl.delete_slice(
                **{'s_id': s_id, 'type': self.s_ids[s_id]})

            # Inform the user about the removal
            return success, msg

        # Remove the service from the list of service IDs
        del self.s_ids[s_id]


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        wireless_orchestrator_thread = wireless_orchestrator_server(
            host='127.0.0.1',
            port=2100,



        )
        wireless_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wireless Orchestrator Server
        print('Exiting')
        wireless_orchestrator_thread.shutdown_flag.set()
        wireless_orchestrator_thread.join()
