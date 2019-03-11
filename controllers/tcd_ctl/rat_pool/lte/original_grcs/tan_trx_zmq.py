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
import hydra
import threading


class tan_trx_zmq(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tan Trx Zmq")

        ##################################################
        # Variables
        ##################################################
        self.xvl_port = xvl_port = 5000
        self.xvl_host = xvl_host = '127.0.0.1'
        self.tx_offset = tx_offset = -1e6
        self.samp_rate = samp_rate = 1e6
        self.rx_offset = rx_offset = +1e6
        self.rat_id = rat_id = 2
        self.payload_size = payload_size = 1000
        self.centre_frequency = centre_frequency = 3.75e9

        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_sink_0 = hydra.hydra_gr_client_sink(rat_id, xvl_host, xvl_port)
        self.hydra_gr_sink_0.start_client(centre_frequency + tx_offset, samp_rate, payload_size)
        self.hydra_gr__source_0_0 = hydra.hydra_gr_client_source(rat_id, xvl_host, xvl_host, xvl_port)
        self.hydra_gr__source_0_0.start_client(centre_frequency + rx_offset, samp_rate, payload_size)

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
        	  frame_length_tag_key='frame_'+'packet_len',
        	  packet_length_tag_key='packet_len',
        	  bps_header=1,
        	  bps_payload=1,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(rat_id), 1000, True)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'packet_len')

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.hydra_gr_sink_0, 0))
        self.connect((self.hydra_gr__source_0_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_xvl_port(self):
        return self.xvl_port

    def set_xvl_port(self, xvl_port):
        self.xvl_port = xvl_port

    def get_xvl_host(self):
        return self.xvl_host

    def set_xvl_host(self, xvl_host):
        self.xvl_host = xvl_host

    def get_tx_offset(self):
        return self.tx_offset

    def set_tx_offset(self, tx_offset):
        self.tx_offset = tx_offset

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_rx_offset(self):
        return self.rx_offset

    def set_rx_offset(self, rx_offset):
        self.rx_offset = rx_offset

    def get_rat_id(self):
        return self.rat_id

    def set_rat_id(self, rat_id):
        self.rat_id = rat_id

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size

    def get_centre_frequency(self):
        return self.centre_frequency

    def set_centre_frequency(self, centre_frequency):
        self.centre_frequency = centre_frequency


def main(top_block_cls=tan_trx_zmq, options=None):

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
