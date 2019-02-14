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
    source_port = kwargs.get('source_port', 1201)
    ip = kwargs.get('ip', '127.0.0.1')
    destination_port = kwargs.get('destination_port', 1501)
    port_offset = kwargs.get('port_offset', 0)

    usrp_address = kwargs.get('usrp', "serial=30C6272")
    samp_rate = kwargs.get('samp_rate', 1e6)
    gain = kwargs.get('gain', 1)
    centre_freq = kwargs.get('centre_freq', 2e9)

    source_address = 'tcp://' + ip + ':' + str(source_port + port_offset)
    destination_address = 'tcp://' + ip + ':' + str(destination_port +
                                                    port_offset)

    ##################################################
    # Blocks
    ##################################################
    zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1,
                                          destination_address, 100, True, -1)

    zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1,
                                              source_address, 100, True, -1)
    uhd_usrp_source_0 = uhd.usrp_source(
        ",".join((usrp_address, "")),
        uhd.stream_args(
            cpu_format="fc32",
            channels=range(1),
        ),
    )

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
    parser = argparse.ArgumentParser(description='ZMQ USRP Transciever')

    # Add CLI arguments
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='IP')
    parser.add_argument(
        '--source_port', type=int, default=1201, help='source port')
    parser.add_argument(
        '--destination_port', type=int, default=1501, help='destination port')
    parser.add_argument(
        '--port_offset',
        type=int,
        default=0,
        help='add a port offset to the source and destination ports')

    parser.add_argument(
        '--usrp', type=str, default="serial=30C6272", help='USRP Address')
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
