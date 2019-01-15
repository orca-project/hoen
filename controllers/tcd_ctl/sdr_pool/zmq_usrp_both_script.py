#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Zmq Usrp Both
# Generated: Thu Nov 29 07:36:38 2018
##################################################


from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time
import argparse


def zmq_usrp_both(**kwargs):
    # Top block instance
    tb = gr.top_block()
    ##################################################
    # Variables
    ##################################################
    port = kwargs.get('port', 6000)
    ip = kwargs.get('ip', '127.0.0.1')
    usrp_address = kwargs.get('usrp', '192.168.0.3')
    usrp_subdev = kwargs.get('subdev', 'A:A')
    samp_rate = kwargs.get('samp_rate', 1e6)
    gain = kwargs.get('gain', 1)
    centre_freq = kwargs.get('centre_freq', 2e9)
    server_address = 'tcp://' + ip + ':' + str(port)
    server_address_0 = 'tcp://' + ip + ':' + str(port+1)


    ##################################################
    # Blocks
    ##################################################
    zeromq_push_sink_0 = zeromq.push_sink(
        gr.sizeof_gr_complex,
        1,
        server_address,
        100,
        False,
        -1)

    zeromq_pull_source_0 = zeromq.pull_source(
        gr.sizeof_gr_complex,
        1,
        server_address_0,
        100,
        False,
        -1)

    uhd_usrp_source_0 = uhd.usrp_source(
        ",".join((usrp_address, "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    uhd_usrp_source_0.set_subdev_spec(usrp_subdev, 0)
    uhd_usrp_source_0.set_samp_rate(samp_rate)
    uhd_usrp_source_0.set_center_freq(centre_freq, 0)
    uhd_usrp_source_0.set_normalized_gain(gain, 0)
    uhd_usrp_source_0.set_antenna('RX2', 0)
    uhd_usrp_source_0.set_bandwidth(samp_rate, 0)

    uhd_usrp_sink_0 = uhd.usrp_sink(
        ",".join((usrp_address, "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    uhd_usrp_sink_0.set_subdev_spec(usrp_subdev, 0)
    uhd_usrp_sink_0.set_samp_rate(samp_rate)
    uhd_usrp_sink_0.set_center_freq(centre_freq, 0)
    uhd_usrp_sink_0.set_normalized_gain(gain, 0)
    uhd_usrp_sink_0.set_antenna('TX/RX', 0)
    uhd_usrp_sink_0.set_bandwidth(samp_rate, 0)

    ##################################################
    # Connections
    ##################################################
    tb.connect((uhd_usrp_source_0, 0), (zeromq_push_sink_0, 0))
    tb.connect((zeromq_pull_source_0, 0), (uhd_usrp_sink_0, 0))


    # Start the boombox
    tb.run()

def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='ZMQ USRP Both (Transciever)')
    # Add CLI arguments
    parser.add_argument(
        '--port', type=int, default=5000, help='ZMQ Port')
    parser.add_argument(
        '--ip', type=str, default='127.0.01', help='ZMQ IP')
    parser.add_argument(
        '--usrp', type=str,  default='192.168.0.2', help='USRP Address')
    parser.add_argument(
        '--subdev', type=str, default=' A:A', help='USRP Subdev')
    parser.add_argument(
        '--rate', type=float, default=1e6, help='Sampling Rate')
    parser.add_argument(
        '--freq', type=float, default=2e9, help='Centre Frequency')
    parser.add_argument(
        '--gain', type=float, default=1.0, help='Normalised Gain')

    # Parse and return CLI arguments
    return vars(parser.parse_args())


if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    zmq_usrp_both(**kwargs)
