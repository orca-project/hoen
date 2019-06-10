#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Server Hydra
# Generated: Wed Mar 13 02:51:40 2019
##################################################

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt5 import Qt, QtCore
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import hydra
import sys
import threading
from gnuradio import qtgui
import argparse
import signal

class hydra_server(object):

    def __init__(self, **kwargs):

        # Top block instance
        self.tb = gr.top_block()
        ##################################################
        # Variables
        ##################################################
        self.host = kwargs.get('host', '127.0.0.1')
        self.port = kwargs.get('port', 5000)
        self.tx_centre_freq = kwargs.get('tx_centre_freq', 3.75e9)
        self.tx_samp_rate = kwargs.get('tx_samp_rate', 2e6)
        self.tx_fft_size = kwargs.get('tx_fft_size', 1024)
        self.rx_centre_freq = kwargs.get('rx_centre_freq', 3.75e9)
        self.rx_samp_rate = kwargs.get('rx_samp_rate', 2e6)
        self.rx_fft_size = kwargs.get('rx_fft_size', 1024)

        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_server_0 = hydra.hydra_gr_server(self.host + ":" + str(self.port))
        if self.tx_centre_freq > 0 and self.tx_samp_rate > 0 and self.tx_fft_size > 0:
           self.hydra_gr_server_0.set_tx_config(self.tx_centre_freq, self.tx_samp_rate, self.tx_fft_size, "USRP")
        if self.rx_centre_freq > 0 and self.rx_samp_rate > 0 and self.rx_fft_size > 0:
           self.hydra_gr_server_0.set_rx_config(self.rx_centre_freq, self.rx_samp_rate, self.rx_fft_size, "USRP")

        print('TX', 'CF', self.tx_centre_freq, 'BW', self.tx_samp_rate, 'FFT', self.tx_fft_size)
        print('RX', 'CF', self.rx_centre_freq, 'BW', self.rx_samp_rate, 'FFT', self.rx_fft_size)

    def run(self):
        self.hydra_gr_server_0_thread = threading.Thread(target=self.hydra_gr_server_0.start_server)
        self.hydra_gr_server_0_thread.daemon = True
        self.hydra_gr_server_0_thread.start()

        self.tb = top_block_cls()
        self.tb.start()

    def exit(self, *args):
        self.tb.stop()
        self.tb.wait()

def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='HyDRA Server Script')
    # Add CLI arguments
    parser.add_argument(
        '--host', type=str, default='127.0.0.1', help='HyDRA Host')
    parser.add_argument(
        '--port', type=int, default=5000, help='HyDRA Port')
    parser.add_argument(
        '--tx_centre_freq', type=float, default=3.75e9, help='TX Centre Frequency')
    parser.add_argument(
        '--rx_centre_freq', type=float, default=3.75e9, help='RX Centre Frequency')
    parser.add_argument(
        '--tx_samp_rate', type=float, default=2e6, help='TX Sampling Rate')
    parser.add_argument(
        '--rx_samp_rate', type=float, default=2e6, help='RX Sampling Rate')
    parser.add_argument(
        '--tx_fft_size', type=int, default=1024, help='TX FFT Size')
    parser.add_argument(
        '--rx_fft_size', type=int, default=1024, help='RX FFT Size')

    # Parse and return CLI arguments
    return vars(parser.parse_args())

if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    my_hydra = hydra_server(**kwargs)

    signal.signal(signal.SIGINT, my_hydra.exit)
    signal.signal(signal.SIGTERM, my_hydra.exit)

    my_hydra.run()

    signal.pause()

