#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tan Trx Zmq
# Generated: Mon Mar 11 13:20:21 2019
##################################################

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import argparse
import hydra
import threading


def tan_trx_zmq(**kwargs):
    # Top block instance
    tb = gr.top_block()
    ##################################################
    # Variables
    ##################################################
    xvl_host = kwargs.get('xvl_host', '127.0.0.1')
    xvl_port = kwargs.get('xvl_port', 5000)
    tx_offset = kwargs.get('tx_offset', -1e6)
    rx_offset = kwargs.get('rx_offset', +1e6)
    samp_rate = kwargs.get('samp_rate', 1e6)
    centre_frequency = kwargs.get('centre_freq', 3.75e9)
    rat_id = kwargs.get('rat_id', 1)
    payload_size = kwargs.get('payload_size', 1000)

    ##################################################
    # Blocks
    ##################################################
    hydra_gr_sink_0 = hydra.hydra_gr_client_sink(rat_id, xvl_host, xvl_port)

    hydra_gr_sink_0.start_client(centre_frequency + tx_offset, samp_rate,
                                 payload_size)

    hydra_gr__source_0_0 = hydra.hydra_gr_client_source(
        rat_id, xvl_host, xvl_host, xvl_port)

    hydra_gr__source_0_0.start_client(centre_frequency + rx_offset, samp_rate,
                                      payload_size)

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

    blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(rat_id), 1000, True)

    blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(
        blocks.byte_t, 'packet_len')

    blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(
        blocks.byte_t, 'packet_len')

    ##################################################
    # Connections
    ##################################################
    tb.msg_connect((blocks_tagged_stream_to_pdu_0, 'pdus'),
                   (blocks_tuntap_pdu_0, 'pdus'))

    tb.msg_connect((blocks_tuntap_pdu_0, 'pdus'),
                   (blocks_pdu_to_tagged_stream_0, 'pdus'))

    tb.connect((blocks_pdu_to_tagged_stream_0, 0), (digital_ofdm_tx_0, 0))

    tb.connect((digital_ofdm_rx_0, 0), (blocks_tagged_stream_to_pdu_0, 0))

    tb.connect((digital_ofdm_tx_0, 0), (hydra_gr_sink_0, 0))

    tb.connect((hydra_gr__source_0_0, 0), (digital_ofdm_rx_0, 0))

    # Start the boombox
    tb.run()


def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='RAT Transceiver')
    # Add CLI arguments
    parser.add_argument(
        '--xvl_host', type=str, default='127.0.0.1', help='XVL Host')
    parser.add_argument('--xvl_port', type=int, default=5000, help='XVL Port')
    parser.add_argument(
        '--tx_offset', type=float, default=-1e6, help='TX Frequency offset')
    parser.add_argument(
        '--rx_offset', type=float, default=+1e6, help='RX Frequency offset')
    parser.add_argument(
        '--samp_rate', type=float, default=1e6, help='Sampling Rate')
    parser.add_argument(
        '--centre_frequency',
        type=float,
        default=3.75e9,
        help='Centre Frequency')
    parser.add_argument(
        '--rat_id', type=int, default=1, help='Virtual Radio ID')
    parser.add_argument(
        '--payload_size', type=int, default=1000, help='Payload Size')

    # Parse and return CLI arguments
    return vars(parser.parse_args())


if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    tan_trx_zmq(**kwargs)
