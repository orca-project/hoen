#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Trx Atempt
# Generated: Wed Mar 13 12:28:51 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time


class trx_atempt(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Trx Atempt")

        ##################################################
        # Variables
        ##################################################
        self.txo = txo = -0.5e6
        self.samp_rate = samp_rate = 500e3
        self.rxo = rxo = 0.5e6
        self.cf = cf = 3.75e9

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(cf + rxo, 0)
        self.uhd_usrp_source_0.set_normalized_gain(.3, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(cf + txo, 0)
        self.uhd_usrp_sink_0.set_normalized_gain(0.85, 0)
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
        self.blocks_tag_debug_0 = blocks.tag_debug(gr.sizeof_char*1, '', ""); self.blocks_tag_debug_0.set_display(True)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'packet_len')
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.6, ))

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.blocks_tag_debug_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tag_debug_1, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_txo(self):
        return self.txo

    def set_txo(self, txo):
        self.txo = txo
        self.uhd_usrp_sink_0.set_center_freq(self.cf + self.txo, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_rxo(self):
        return self.rxo

    def set_rxo(self, rxo):
        self.rxo = rxo
        self.uhd_usrp_source_0.set_center_freq(self.cf + self.rxo, 0)

    def get_cf(self):
        return self.cf

    def set_cf(self, cf):
        self.cf = cf
        self.uhd_usrp_source_0.set_center_freq(self.cf + self.rxo, 0)
        self.uhd_usrp_sink_0.set_center_freq(self.cf + self.txo, 0)


def main(top_block_cls=trx_atempt, options=None):

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
