#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template SDR Controller
from template_controllers.sdr_controller import sdr_controller_template
# Import OS
import os
# Import signal
import signal

from grc_manager import grc_manager


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


class tcd_controller(sdr_controller_template):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting TCD Controller')
        self.grc_manager = grc_manager()

        self.usrp = self.grc_manager.create_sdr()

    def pre_exit(self):
     # Terminate the TCD SDR Controller Server
        self.shutdown_flag.set()
        # Release SDRs
        self.grc_manager.remove_sdr()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # TCD: This is where you must create a radio slice

        # If succeeded creating the slice
        if True:
            # TODO We treat the radio slice as a network sink
            # Send ACK
            msg = {'nl_ack': {'host': "<IP>", "port": 7001}}

        # If failed creating slice
        else:
            # Send NACK
            msg = {'nl_nack': {'<Reason for failing>'}}

            # TODO You can use any logic you want. We just need the
            # resulting messages formatted like above

        # TODO Call this after the virtual radio was created
        self.grc_manager.create_rat(tech='lte')

        return msg

    def remove_slice(self, **kwargs):
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # TCD: This is where you must remove a radio slice

        # If succeeded removing the slice
        if True:
            # Send ACK
            msg = {'rl_ack': {'s_id': kwargs['s_id']}}

        # If failed removing slice
        else:
            # Send NACK
            msg = {'rl_nack': {'<Reason for failing>'}}

            # TODO You can use any logic you want. We just need the
            # resulting messages formatted like above

        # TODO Call this before the virtual radio is removed
        self.grc_manager.remove_rat(tech='lte')

        return msg


if __name__ == "__main__":
    # Clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the TCD SDR Controller
        tcd_controller_thread = tcd_controller(
            name='TCD',
            req_header='tcd_req',  # Don't modify
            rep_header='tcd_rep',  # Don't modify
            host='127.0.0.1',
            port=7000)

        # Start the TCD SDR Controller Server
        tcd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TCD SDR Controller Server
        tcd_controller_thread.pre_exit()

        print('Exiting')
