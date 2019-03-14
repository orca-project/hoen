#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Enb Hydra
# Generated: Wed Mar 13 22:53:14 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import hydra
import threading
import argparse
import signal

class enb(object):
    def __init__(self, **kwargs):
        # Top block instance
        self.tb = gr.top_block()
        ##################################################
        # Variables
        ##################################################
        self.host = kwargs.get('xvl_host', '127.0.0.1')
        self.port = kwargs.get('xvl_port', 5000)
        self.cf = kwargs.get('centre_frequency', 3.75e9)
        self.samp_rate = kwargs.get('samp_rate', 500e3)
        self.rat_id = kwargs.get('rat_id', 1)

        ##################################################
        # Variables
        ##################################################
        self.txo = 0.5e6
        self.rxo = -0.5e6

        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_sink_0 = hydra.hydra_gr_client_sink(self.rat_id, self.host, self.port)
        self.hydra_gr_sink_0.start_client(self.cf+self.txo, self.samp_rate, 1000)
        self.hydra_gr__source_0 = hydra.hydra_gr_client_source(self.rat_id, self.host, self.host, self.port)
        self.hydra_gr__source_0.start_client(self.cf+self.rxo, self.samp_rate, 1000)

        self.digital_ofdm_tx_0 = digital.ofdm_tx(
        	  fft_len=64, cp_len=16,
        	  packet_length_tag_key='packet_len',
        	  bps_header=1,
        	  bps_payload=1,
        	  rolloff=0,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.digital_ofdm_rx_0 = digital.ofdm_rx(
        	  fft_len=64, cp_len=16,
        	  frame_length_tag_key='frame_'+"length",
        	  packet_length_tag_key="length",
        	  bps_header=1,
        	  bps_payload=1,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(self.rat_id), 1000, False)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'length')
        self.blocks_tag_debug_1 = blocks.tag_debug(gr.sizeof_char*1, '', ""); self.blocks_tag_debug_1.set_display(True)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'packet_len')
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.01, ))

    def run(self):
        ##################################################
        # Connections
        ##################################################
        self.tb.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.tb.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.tb.connect((self.blocks_multiply_const_vxx_0, 0), (self.hydra_gr_sink_0, 0))
        self.tb.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.tb.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tag_debug_1, 0))
        self.tb.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.tb.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.tb.connect((self.hydra_gr__source_0, 0), (self.digital_ofdm_rx_0, 0))


        # Start the boombox
        self.tb.start()

    def exit(self, *args):
        self.tb.stop()
        self.tb.wait()

        del self.hydra_gr_sink_0
        del self.hydra_gr__source_0_0

def get_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Virtual Radio')
    # Add CLI arguments
    parser.add_argument(
        '--xvl_host', type=str, default='127.0.0.1', help='XVL Host')
    parser.add_argument('--xvl_port', type=int, default=5000, help='XVL Port')
    parser.add_argument(
        '--samp_rate', type=float, default=500e3, help='Sampling Rate')
    parser.add_argument(
        '--centre_frequency',
        type=float,
        default=3.75e9,
        help='Centre Frequency')
    parser.add_argument(
        '--rat_id', type=int, default=1, help='Virtual Radio ID')

    # Parse and return CLI arguments
    return vars(parser.parse_args())


if __name__ == '__main__':
    # Get CLI arguments as a dictionary
    kwargs = get_args()
    # Call the main function
    my_radio= enb(**kwargs)

    signal.signal(signal.SIGINT, my_radio.exit)
    signal.signal(signal.SIGTERM, my_radio.exit)

    my_radio.run()

    signal.pause()
