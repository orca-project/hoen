#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import OS
import os
# Import signal
import signal


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


class imec_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting IMEC Controller')

    def pre_exit(self):
     # Terminate the IMEC SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Check for missing S_ID
        if s_id is None:
            # Return NACK
            return False, 'Missing Service ID.'

        # TODO do something here

        if True:
            # Return host
            return True, {'host': '127.0.0.1'}

        if False:
            return False, "<Reason for failing>"


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Check for missing S_ID
        if s_id is None:
            # Return NACK
            return False, 'Missing Service ID.'

        # TODO do something here

        if True:
            # Return host
            return True, {'s_id': kwargs['s_id']}

        if False:
            return False, "<Reason for failing>"

if __name__ == "__main__":
    # Clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the IMEC SDR Controller
        imec_controller_thread = imec_controller(
            name='IMEC',
            req_header='imec_req', # Don't modify
            rep_header='imec_rep', # Don't modify
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            host='127.0.0.1',
            port=3200)

        # Start the IMEC SDR Controller Server
        imec_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the IMEC SDR Controller Server
        imec_controller_thread.pre_exit()

        print('Exiting')
