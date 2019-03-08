#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal

import argparse

#  from flow_manager import flow_manager

def cls():
    system('cls' if name == 'nt' else 'clear')


class ovs_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting OVS Controller')
        # Start the OVS manager
        #  self.flow_manager = flow_manager()

    def pre_exit(self):
     # Terminate the OVS SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        tech = kwargs.get('type', 'high-throughput')
        s_id = kwargs.get('s_id', None)

        # Return host and port -- TODO may drop port entirely
        return True, {'host': host}


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Third step: Remove virtual RF front-end
        # TODO do something here


        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': kwargs['s_id']}


def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='OVS Controller')

    # Add CLI arguments
    parser.add_argument(
        '--host', type=str, default='127.0.0.1', help='Controller Server IP')
    parser.add_argument(
        '--port', type=int, default=3300, help='Controller Port')


    # Parse and return CLI arguments
    return vars(parser.parse_args())

if __name__ == "__main__":
    # Clear screen
    cls()

    # Get CLI arguments
    kwargs = get_args()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the OVS SDR Controller
        ovs_controller_thread = ovs_controller(
            name='OVS',
            req_header='ovs_req', # Don't modify
            rep_header='ovs_rep', # Don't modify
            create_msg='wdc_crs',
            request_msg='wdc_rrs',
            update_msg='wdc_urs',
            delete_msg='wdc_drs',
            host=kwargs.get('host', '127.0.0.1'),
            port=kwargs.get('port', 3300)
        )

        # Start the OVS SDR Controller Server
        ovs_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the OVS SDR Controller Server
        ovs_controller_thread.pre_exit()

        print('Exiting')
