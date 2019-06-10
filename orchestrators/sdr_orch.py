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
import time 

def cls():
    system('cls' if name=='nt' else 'clear')

class wireless_orchestrator_server(base_orchestrator):

    def post_init(self, **kwargs):
        # IMEC Controller Handler
        self.imec_ctl = ctl_base(
            name="IMEC",
            host_key="imec_host",
            port_key="imec_port",
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            default_host="10.2.0.1",
            default_port="6000",
            request_key="imec_req",
            reply_key="imec_rep")

        # TCD Controller Handler
        self.tcd_ctl = ctl_base(
            name="TCD",
            host_key="tcd_host",
            port_key="tcd_port",
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            default_host="10.1.0.1",
            default_port="3200",
            request_key="tcd_req",
            reply_key="tcd_rep")

    def create_slice(self, **kwargs):
        st = time.time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        s_type = kwargs.get('type', None)

        # Append it to the list of service IDs
        self.s_ids[s_id] = s_type

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


        elif s_type == "low-latency":
            # Send messate to IMEC SDR Controller
            print('\t', 'Traffic type: Low Latency')
            print('\t', 'Delegating it to the IMEC Controller')

            # Send the message to create a slice
            success, msg = self.imec_ctl.create_slice(
              **{'s_id': s_id, 's_type': s_type})
            #  success = True
            #  msg = {'host': '10.1.1.1'}


            print('returned', (time.time()-st)*1000, 'ms')
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
            return False, msg


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

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


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        wireless_orchestrator_thread = wireless_orchestrator_server(
            name='SDR',
            req_header='sdr_req',
            rep_header='sdr_rep',
            error_msg='msg_err',
            create_msg='wl_cr',
            request_msg='wl_rr',
            update_msg='wl_ur',
            delete_msg='wl_dr',
            host='10.0.0.2',
            port=2100
        )

        wireless_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wireless Orchestrator Server
        print('Exiting')
        wireless_orchestrator_thread.shutdown_flag.set()
        wireless_orchestrator_thread.join()
