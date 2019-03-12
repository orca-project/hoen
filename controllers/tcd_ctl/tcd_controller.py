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

from subprocess import Popen, PIPE
from os import setsid, getpgid

from grc_manager import grc_manager
from route_manager import route_manager
from xvl_manager import xvl_client


def cls():
    system('cls' if name == 'nt' else 'clear')


class vr(object):
    def __init__(self, **kwargs):
        self.free = True
        self.s_id = kwargs.get('s_id', '')
        self.vfe = kwargs.get('vfe', None)
        self.grc = kwargs.get('grc', None)
        self.host = kwargs.get('host', None)
        self.rat_id = kwargs.get('rat_id', 0)


class tcd_controller(base_controller):
    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting TCD Controller')
        # Start the GRC manager
        self.grc_manager = grc_manager()
        # Start the route manager
        self.route_manager = route_manager()

        # TODO Call XVL here
        if False:
            self.xvl_process = Popen(
                '/root/gr-hydra/build/app/server',
                stdout=PIPE,
                stderr=PIPE,
                preexec_fn=setsid)

            self.xvl_p_id = getpgid(self.xvl_process.pid)
            print('- XVL Process: ', self.xvl_p_id)

        # Max number of VRs
        self.max_vrs = 2
        # List of VR objects
        self.virtual_radios = [
            vr(rat_id=x) for x in range(1, self.max_vrs + 1)
        ]

        self.fallback()

    def fallback(self):
        # System centre freq
        centre_freq = 3.75e9
        # Desired GB
        guard_band = 0.5e6
        # Desired Samp rate per channel
        samp_rate = 2e6
        # Offset between channels
        dist = 0.5 * (guard_band + samp_rate)
        # Total BW
        vr_bw = dist * 4
        # Bandwidth of the RF front-end
        rr_bw = 10e6

        for virtual_radio in self.virtual_radios:
            # Centre the virtua; radio at the right place
            vr_cf = centre_freq - (
                0.5 * rr_bw) + (virtual_radio.rat_id - 0.5) * vr_bw

            virtual_radio.vfe = xvl_client(rat_id=virtual_radio.rat_id)

            virtual_radio.vfe.check_connection()
            #  virtual_radio.vfe.check_connection()
            virtual_radio.vfe.tx_port = virtual_radio.vfe.request_tx_resources(
                centre_freq=(vr_cf - dist), bandwidth=samp_rate)

            virtual_radio.vfe.rx_port = virtual_radio.vfe.request_rx_resources(
                centre_freq=(vr_cf + dist), bandwidth=samp_rate)
            
            print('VR', virtual_radio.rat_id,
                  'TX Port', virtual_radio.vfe.tx_port,
                  'RX Port', virtual_radio.vfe.rx_port)

            if not virtual_radio.vfe.tx_port or not virtual_radio.vfe.rx_port:
                print('Could not allocate VR')
                exit()

    def pre_exit(self):
        # Terminate the TCD SDR Controller Server
        self.shutdown_flag.set()
        # Release RATs
        self.grc_manager.remove_rat()
        # Release SDRs
        #  self.grc_manager.remove_sdr()
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

        # First step: Create virtual RF front-end
        # TODO do something here

        virtual_radio = [x for x in self.virtual_radios if x.free]

        if not virtual_radio:
            return False, 'No more Virtual Radios available'

        # Get the first free VR
        else:
            virtual_radio = virtual_radio[0]

        # Second step: Create the RAT
        try:
            # Create a new software radio
            grc = self.grc_manager.create_rat(
                service_id=s_id,
                rat_id=virtual_radio.rat_id,
                tx_port=virtual_radio.vfe.tx_port,
                rx_port=virtual_radio.vfe.rx_port)

        # If failed creating software radio
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        virtual_radio.grc = grc

        print('\t', 'TX Port', virtual_radio.vfe.tx_port)
        print('\t', 'RX Port', virtual_radio.vfe.tx_port)

        # Third step: Configure routes
        try:
            host = self.route_manager.create_route(rat_id=virtual_radio.rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        virtual_radio.host = host

        virtual_radio.free = False
        virtual_radio.s_id = s_id

        for i, x in enumerate(self.virtual_radios):
            if x.rat_id == virtual_radio.rat_id:
                # Update the list of VRs
                self.virtual_radios[i] = virtual_radio

        # Return host and port -- TODO may drop port entirely
        return True, {'host': host}

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        virtual_radio = [x for x in self.virtual_radios if x.s_id == s_id][0]

        #First Step: Remove the RAT
        try:
            # Remove a software radio
            self.grc_manager.remove_rat(service_id=s_id)

        # If it failed removing the software radio
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        # Second step: Remove routes
        try:
            self.route_manager.remove_route(rat_id=virtual_radio.rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return False, str(e)

        # Third step: Remove virtual RF front-end
        # TODO do something here

        virtual_radio.free = True
        virtual_radio.host = ''
        virtual_radio.s_id = ''

        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': kwargs['s_id']}


def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='ZMQ USRP Transciever')

    # Add CLI arguments
    parser.add_argument(
        '--centre_freq_tx',
        type=float,
        default=2e9 - 1e6,
        help='tx centre frequency')
    parser.add_argument(
        '--centre_freq_rx',
        type=float,
        default=2e9 + 1e6,
        help='rx centre frequency')
    parser.add_argument(
        '--samp_rate_tx', type=float, default=1e6, help='tx samp rate')
    parser.add_argument(
        '--samp_rate_rx', type=float, default=1e6, help='rx samp rate')
    parser.add_argument('--gain_tx', type=float, default=1, help='tx gain')
    parser.add_argument('--gain_rx', type=float, default=1, help='rx gain')
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
            req_header='tcd_req',  # Don't modify
            rep_header='tcd_rep',  # Don't modify
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            host=kwargs.get('host', '127.0.0.1'),
            port=kwargs.get('port', 3200),
            centre_freq_tx=kwargs.get('centre_freq_tx', 2e9 - 1e6),
            centre_freq_rx=kwargs.get('centre_freq_rx', 2e9 + 1e6),
            samp_rate_tx=kwargs.get('samp_rate_tx', 1e6),
            samp_rate_rx=kwargs.get('samp_rate_rx', 1e6),
            gain_tx=kwargs.get('gain_tx', 1),
            gain_rx=kwargs.get('gain_rx', 1))

        # Start the TCD SDR Controller Server
        tcd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TCD SDR Controller Server
        tcd_controller_thread.pre_exit()

        print('Exiting')
