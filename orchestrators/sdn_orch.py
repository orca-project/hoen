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

class wired_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # IMEC Controller Handler
        self.ovs_ctl = ctl_base(
            name="OVS",
            host_key="ovs_host",
            port_key="ovs_port",
            default_host="10.0.0.5",
            default_port="3300",
            request_key="ovs_req",
            reply_key="ovs_rep",
            create_msg='wdc_crs',
            request_msg='wdc_rrs',
            update_msg='wdc_urs',
            delete_msg='wdc_drs')


    def create_slice(self, **kwargs):
        st = time.time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        s_type = kwargs.get('type', None)

        # Append it to the list of service IDs
        self.s_ids[s_id] = s_type

        if s_type not in ["high-throughput", "low-latency"]:
            # Send error message
            msg = 'Could not identify the traffic type:' + str(s_type)

            print('failed', (time.time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg


        # Send message to OVS SDN controller
        print('\t', 'Traffic type: ' + str(s_type).title())
        print('\t', 'Delegating it to the OVS Controller')

        # Send the message to create a slice
        success, msg = self.ovs_ctl.create_slice(
                **{'s_id': s_id,
                    'type': s_type,
                    'destination': kwargs.get('destination')
                    })

        print('success', (time.time()-st)*1000, 'ms')
        # Inform the user about the creation
        return success, msg

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Ge the slice type
        s_type = self.s_ids[s_id]

        # Send message to OVS SDN controller
        print('\t', 'Traffic type: ' + str(s_type).title())
        print('\t', 'Delegating it to the OVS Controller')

        # Send message to remove slice
        success, msg = self.ovs_ctl.delete_slice(**{'s_id': s_id,
                                                    'type': s_type})

        # Inform the user about the removal
        return success, msg


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Wired Network Orchestrator thread
        wired_orchestrator_thread = wired_orchestrator(
            name='SDN',
            req_header='sdn_req',
            rep_header='sdn_rep',
            error_msg='msg_err',
            create_msg='wd_cc',
            request_msg='wd_rc',
            update_msg='wd_uc',
            delete_msg='wd_dc',
            host='10.0.0.2',
            port=2200
        )

        # Start the Wired Network Orchestrator
        wired_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wired Orchestrator Server
        print('Exiting')
        wired_orchestrator_thread.shutdown_flag.set()
        wired_orchestrator_thread.join()
