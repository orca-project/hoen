#!/usr/bin/env python3
# Import Signal
import signal
# Import the Template SDR Controller
from template_controllers.sdr_controller import sdr_controller_template

class ServiceExit(Exception):
    pass


def signal_handler(sig, frame):
    # Raise ServiceExit upon call
    raise ServiceExit


class imec_controller(sdr_controller_template):

    def create_slice(self, **kwargs):
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # IMEC: This is where you must create a radio slice

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

        return msg


    def remove_slice(self, **kwargs):
        # TODO Please see it here!
        # TODO This is a stub.
        # TODO Please fill this with the required functionality.

        # IMEC: This is where you must remove a radio slice

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


if __name__ == "__main__":
    # Catch SIGTERM and SIGINT signals
    # signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Instantiate the IMEC SDR Controller
        imec_controller_thread = imec_controller(
            name='IMEC',
            req_header='imec_req', # Don't modify
            rep_header='imec_rep', # Don't modify
            host='127.0.0.1',
            port=6000)

        # Start the IMEC SDR Controller Server
        imec_controller_thread.start()

    except ServiceExit:
        # Terminate the IMEC SDR Controller Server
        imec_controller_thread.shutdown_flag.set()
        print('Exitting')
