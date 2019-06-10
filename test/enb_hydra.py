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


class enb_hydra(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Enb Hydra")

        ##################################################
        # Variables
        ##################################################
        self.txo = txo = 0.5e6
        self.samp_rate = samp_rate = 500e3
        self.rxo = rxo = -0.5e6
        self.cf = cf = 3.75e9

        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_sink_0 = hydra.hydra_gr_client_sink(2, '127.0.0.1', 5000)
        self.hydra_gr_sink_0.start_client(cf+txo, samp_rate, 1000)
        self.hydra_gr__source_0 = hydra.hydra_gr_client_source(2, '127.0.0.1', '127.0.0.1', 5000)
        self.hydra_gr__source_0.start_client(cf+rxo, samp_rate, 1000)

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
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap0', 1000, False)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'length')
        self.blocks_tag_debug_1 = blocks.tag_debug(gr.sizeof_char*1, '', ""); self.blocks_tag_debug_1.set_display(True)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'packet_len')
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.01, ))

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.hydra_gr_sink_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tag_debug_1, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.hydra_gr__source_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_txo(self):
        return self.txo

    def set_txo(self, txo):
        self.txo = txo

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_rxo(self):
        return self.rxo

    def set_rxo(self, rxo):
        self.rxo = rxo

    def get_cf(self):
        return self.cf

    def set_cf(self, cf):
        self.cf = cf


def main(top_block_cls=enb_hydra, options=None):

    tb = top_block_cls()
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
