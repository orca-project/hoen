#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import OS
import os
# Import signal
import signal


class example_controller(base_controller):

    def post_init(self, **kwargs):
        pass

    def create_slice(self, **kwargs):
       # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))

        # Return state
        return True, "This is a stub"


    def request_slice(self, **kwargs):
       # Extract parameters from keyword arguments
       s_id = kwargs.get('s_id', None)

       # Return state
       return True, "This is a stub"


    def update_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', none)

        # Return state
        return true, "This is a stub"


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', none)

        # Return state
        return true, "This is a stub"


if __name__ == "__main__":
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Example Controller
        example_controller_thread = example_controller(
            name='Example',
            req_header='ex_req',  # Don't modify
            rep_header='ex_rep',  # Don't modify
            create_msg='ex_ces',
            request_msg='ex_res',
            update_msg='ex_ues',
            delete_msg='ex_des',
            host='0.0.0.0',
            port=10000)

        # Start the Example Controller Server
        example_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Example Controller Server
        example_controller_thread.safe_shutdown()
