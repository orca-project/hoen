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

class example_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # Controller Handler
        self.ctl = ctl_base(
            name="CTL",
            host_key="ctl_host",
            port_key="ctl_port",
            default_host="127.0.0.1",
            default_port="10000",
            request_key="ctl_req",
            reply_key="ctl_rep",
            create_msg='ctl_crs',
            request_msg='ctl_rrs',
            update_msg='ctl_urs',
            delete_msg='ctl_drs')

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Inform the user about the creation
        return True, "This is a stub."

    def request_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Inform the user about the creation
        return True, "This is a stub."

    def update_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Inform the user about the creation
        return True, "This is a stub."

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Inform the user about the creation
        return True, "This is a stub."


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate Example Orchestrator thread
        example_orchestrator_thread = example_orchestrator(
            name='example',
            req_header='ex_req',
            rep_header='ex_rep',
            error_msg='msg_err',
            create_msg='ex_cc',
            request_msg='ex_rc',
            update_msg='ex_uc',
            delete_msg='ex_dc',
            host='127.0.0.1',
            port=11000)

        # Start the Example Orchestrator
        example_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Example Orchestrator Server
        example_rchestrator_thread.safe_shutdown()
