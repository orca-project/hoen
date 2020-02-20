#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tan Trx Zmq
# Generated: Tue Feb 12 16:34:02 2019
##################################################

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import argparse


def tan_trx_zmq(**kwargs):
    # Top block instance
    tb = gr.top_block()
    ##################################################
    # Variables
    ##################################################
    source_ip = kwargs.get('source_ip', '127.0.0.1')
    source_port = kwargs.get('source_port', 500)
    destination_ip = kwargs.get('destination_ip', '127.0.0.1')
    destination_port = kwargs.get('destination_port', 200)
    rat_id = kwargs.get('rat_id', 0)
    digital_gain = kwargs.get('digital_gain', 0.06)
    #  packet_len = kwargs.get('packet_len', 84)

    # Form the source and destination addresses
    source_address = 'tcp://' + source_ip + ':' + str(source_port)
    destination_address = 'tcp://' + destination_ip + ':' + \
        str(destination_port)

    print(source_address)
    print(destination_address)

    ##################################################
    # Blocks
    ##################################################
    zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1,
                                          destination_address, 100, True, -1)
    zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1,
                                              source_address, 100, True, -1)

    digital_ofdm_tx_0 = digital.ofdm_tx(
        fft_len=64,
        cp_len=16,
        packet_length_tag_key='packet_len',
        bps_header=1,
        bps_payload=1,
        rolloff=0,
        debug_log=False,
        scramble_bits=False)
    digital_ofdm_rx_0 = digital.ofdm_rx(
        fft_len=64,
        cp_len=16,
        frame_length_tag_key='frame_' + 'packet_len',
        packet_length_tag_key='packet_len',
        bps_header=1,
        bps_payload=1,
        debug_log=False,
        scramble_bits=False)

    blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(rat_id), 1000, False)

    blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(
        blocks.byte_t, 'packet_len')

    blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(
        blocks.byte_t, 'packet_len')

    blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((digital_gain, ))

    ##################################################
    # Connections
    ##################################################
    tb.msg_connect((blocks_tagged_stream_to_pdu_0, 'pdus'),
                   (blocks_tuntap_pdu_0, 'pdus'))

    tb.msg_connect((blocks_tuntap_pdu_0, 'pdus'),
                   (blocks_pdu_to_tagged_stream_0, 'pdus'))

    tb.connect((digital_ofdm_tx_0, 0), (blocks_multiply_const_vxx_0, 0))

    tb.connect((blocks_multiply_const_vxx_0, 0), (zeromq_push_sink_0, 0))

    tb.connect((blocks_pdu_to_tagged_stream_0, 0), (digital_ofdm_tx_0, 0))

    tb.connect((zeromq_pull_source_0, 0), (digital_ofdm_rx_0, 0))

    tb.connect((digital_ofdm_rx_0, 0), (blocks_tagged_stream_to_pdu_0, 0))

    # Start the boombox
    tb.run()


def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='RAT Transceiver')
    # Add CLI arguments
    parser.add_argument(
        '--source_ip', type=str, default='127.0.0.1', help='source IP')
    parser.add_argument(
        '--source_port', type=int, default=500, help='source port')
    parser.add_argument(
        '--destination_ip',
        type=str,
        default='127.0.0.1',
        help='destination IP')
    parser.add_argument(
        '--destination_port', type=int, default=200, help='destination port')
    parser.add_argument('--rat_id', type=int, default=0, help='RAT ID')
    parser.add_argument(
        '--digital_gain', type=float, default=0.06, help='Digital Gain')

    # Parse and return CLI arguments
    return vars(parser.parse_args())


if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    tan_trx_zmq(**kwargs)