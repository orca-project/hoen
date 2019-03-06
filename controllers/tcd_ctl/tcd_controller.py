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

from grc_manager import grc_manager
from route_manager import route_manager

def cls():
    system('cls' if name == 'nt' else 'clear')


class tcd_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting TCD Controller')
        # Start the GRC manager
        self.grc_manager = grc_manager()
        # Start the route manager
        self.route_manager = route_manager()

        # Get centre frequency for the real RF front-end
        self.centre_freq_tx = kwargs.get('centre_freq_tx', 2e9-1e6)
        self.centre_freq_rx = kwargs.get('centre_freq_rx', 2e9+1e6)
        self.samp_rate_tx = kwargs.get('samp_rate_tx', 1e6)
        self.samp_rate_rx = kwargs.get('samp_rate_rx', 1e6)
        self.gain_tx = kwargs.get('gain_tx', 1)
        self.gain_rx = kwargs.get('gain_rx', 1)

        # Attach to the USRP and set its centre frequencies, samp rate and gain
        self.usrp = self.grc_manager.create_sdr(
            centre_freq_tx=self.centre_freq_tx,
            centre_freq_rx=self.centre_freq_rx,
            samp_rate_tx=self.samp_rate_tx,
            samp_rate_rx=self.samp_rate_rx,
            gain_tx=self.gain_tx,
            gain_rx=self.gain_rx)


    def pre_exit(self):
     # Terminate the TCD SDR Controller Server
        self.shutdown_flag.set()
        # Release RATs
        self.grc_manager.remove_rat()
        # Release SDRs
        self.grc_manager.remove_sdr()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        tech = kwargs.get('type', 'high-throughput')
        dirx = kwargs.get('dirx', 'trx')
        s_id = kwargs.get('s_id', None)

        # Check for invalid direction
        if dirx not in ['rx', 'tx', 'trx']:
            # Return NACK
            return False, 'Invalid RAT direction: ' + str(dirx)

        # Convert traffic type to RAT
        if tech == 'high-throughput':
            tech = 'lte'
        elif tech == 'low-latency':
            tech = ' iot'
        else:
            # Return NACK
            return False, 'Invalid RAT: ' + str(tech)


        # First step: Create virtual RF front-end
        # TODO do something here


        # Second step: Create the RAT
        try:
            # Create a new software radio
            rat_id = self.grc_manager.create_rat(technology=tech,
                                                 direction=dirx,
                                                 service_id=s_id)

        # If failed creating software radio
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)



        # Third step: Configure routes
        try:
            host = self.route_manager.create_route(rat_id=rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        # Return host and port -- TODO may drop port entirely
        return True, {'host': host}


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        #First Step: Remove the RAT
        try:
            # Remove a software radio
            rat_id = self.grc_manager.remove_rat(s_id=s_id)

        # If it failed removing the software radio
        except Exception as e:
             # Send NACK
            print('\t' + str(e))
            return False, str(e)

        # Second step: Remove routes
        try:
            self.route_manager.remove_route(rat_id=rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        # Third step: Remove virtual RF front-end
        # TODO do something here


        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': kwargs['s_id']}


def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='ZMQ USRP Transciever')

    # Add CLI arguments
    parser.add_argument(
        '--centre_freq_tx', type=int, default=2e9-1e6, help='tx centre frequency')
    parser.add_argument(
        '--centre_freq_rx', type=int, default=2e9+1e6, help='rx centre frequency')
    parser.add_argument(
        '--samp_rate_tx', type=int, default=1e6, help='tx samp rate')
    parser.add_argument(
        '--samp_rate_rx', type=int, default=1e6, help='rx samp rate')
    parser.add_argument(
        '--gain_tx', type=int, default=1, help='tx gain')
    parser.add_argument(
        '--gain_rx', type=int, default=1, help='rx gain')
    parser.add_argument(
        '--host', type=str, default='127.0.0.1', help='Controller Server IP')
    parser.add_argument(
        '--port', type=int, default=3200, help='Controller Port')


    # Parse and return CLI arguments
    return vars(parser.parse_args())

if __name__ == "__main__":
    # Clear screen
    cls()

    # Get CLI arguments
    kwargs = get_args()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the TCD SDR Controller
        tcd_controller_thread = tcd_controller(
            name='TCD',
            req_header='tcd_req', # Don't modify
            rep_header='tcd_rep', # Don't modify
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            host=kwargs.get('host', '127.0.0.1'),
            port=kwargs.get('port', 3200),
            centre_freq_tx=kwargs.get('centre_freq_tx', 2e9-1e6),
            centre_freq_rx=kwargs.get('centre_freq_rx', 2e9+1e6),
            samp_rate_tx=kwargs.get('samp_rate_tx', 1e6),
            samp_rate_rx=kwargs.get('samp_rate_rx', 1e6),
            gain_tx=kwargs.get('gain_tx', 1),
            gain_rx=kwargs.get('gain_rx', 1)
        )

        # Start the TCD SDR Controller Server
        tcd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TCD SDR Controller Server
        tcd_controller_thread.pre_exit()

        print('Exiting')
