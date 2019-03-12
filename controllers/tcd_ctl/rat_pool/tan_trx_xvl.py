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

import signal


class tan_trx_zmq(object):
    def __init__(self, **kwargs):
        # Top block instance
        self.tb = gr.top_block()
        ##################################################
        # Variables
        ##################################################
        self.xvl_host = kwargs.get('xvl_host', '127.0.0.1')
        self.xvl_port = kwargs.get('xvl_port', 5000)
        self.tx_offset = kwargs.get('tx_offset', -1e6)
        self.rx_offset = kwargs.get('rx_offset', +1e6)
        self.samp_rate = kwargs.get('samp_rate', 1e6)
        self.centre_frequency = kwargs.get('centre_frequency', 3.75e9)
        self.rat_id = kwargs.get('rat_id', 1)
        self.payload_size = kwargs.get('payload_size', 1000)
        self.digital_gain = kwargs.get('digital_gain', 0.06)

    def run(self):
        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_sink_0 = hydra.hydra_gr_client_sink(
            self.rat_id, self.xvl_host, self.xvl_port)

        self.hydra_gr_sink_0.start_client(
            self.centre_frequency + self.tx_offset, self.samp_rate,
            self.payload_size)

        self.hydra_gr_source_0_0 = hydra.hydra_gr_client_source(
            self.rat_id, self.xvl_host, self.xvl_host, self.xvl_port)

        self.hydra_gr_source_0_0.start_client(
            self.centre_frequency + self.rx_offset, self.samp_rate,
            self.payload_size)

        print('tx', self.centre_frequency + self.tx_offset)
        print('rx', self.centre_frequency + self.rx_offset)

        self.digital_ofdm_tx_0 = digital.ofdm_tx(
            fft_len=64,
            cp_len=16,
            packet_length_tag_key='packet_len',
            bps_header=1,
            bps_payload=1,
            rolloff=0,
            debug_log=False,
            scramble_bits=False)

        self.digital_ofdm_rx_0 = digital.ofdm_rx(
            fft_len=64,
            cp_len=16,
            frame_length_tag_key='frame_' + 'packet_len',
            packet_length_tag_key='packet_len',
            bps_header=1,
            bps_payload=1,
            debug_log=False,
            scramble_bits=False)

        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(self.rat_id),
                                                     1000, False)

        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(
            blocks.byte_t, 'packet_len')

        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(
            blocks.byte_t, 'packet_len')

        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc(
            (self.digital_gain, ))

        ##################################################
        # Connections
        ##################################################
        self.tb.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'),
                            (self.blocks_tuntap_pdu_0, 'pdus'))

        self.tb.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'),
                            (self.blocks_pdu_to_tagged_stream_0, 'pdus'))

        self.tb.connect((self.blocks_pdu_to_tagged_stream_0, 0),
                        (self.digital_ofdm_tx_0, 0))

        self.tb.connect((self.digital_ofdm_rx_0, 0),
                        (self.blocks_tagged_stream_to_pdu_0, 0))

        self.tb.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))

        self.tb.connect((self.blocks_multiply_const_vxx_0, 0), ((self.hydra_gr_sink_0, 0))

        self.tb.connect((self.hydra_gr_source_0_0, 0),
                        (self.digital_ofdm_rx_0, 0))

        # Start the boombox
        self.tb.start()

    def exit(self, *args):
        self.tb.stop()
        self.tb.wait()

        del self.hydra_gr_sink_0
        del self.hydra_gr_source_0_0


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
    parser.add_argument(
        '--digital_gain', type=float, default=0.06, help='Digital Gain')

    # Parse and return CLI arguments
    return vars(parser.parse_args())


if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    k = tan_trx_zmq(**kwargs)

    signal.signal(signal.SIGINT, k.exit)
    signal.signal(signal.SIGTERM, k.exit)

    k.run()

    signal.pause()
