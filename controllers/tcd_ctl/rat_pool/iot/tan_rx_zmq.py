#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tan Rx Zmq
# Generated: Tue Feb 12 16:24:19 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser


class tan_rx_zmq(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tan Rx Zmq")

        ##################################################
        # Variables
        ##################################################
        self.port = port = 2501
        self.ip = ip = '127.0.0.1'
        self.server_address = server_address = 'tcp://' + ip + ':' + str(port)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1, server_address, 100, False, -1)
        self.digital_ofdm_rx_0 = digital.ofdm_rx(
        	  fft_len=64, cp_len=16,
        	  frame_length_tag_key='frame_'+"len",
        	  packet_length_tag_key="len",
        	  bps_header=1,
        	  bps_payload=1,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.blocks_tuntap_pdu_1 = blocks.tuntap_pdu('tap0', 1000, True)
        (self.blocks_tuntap_pdu_1).set_max_output_buffer(100000)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, "len")

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_1, 'pdus'))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.zeromq_pull_source_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port
        self.set_server_address('tcp://' + self.ip + ':' + str(self.port))

    def get_ip(self):
        return self.ip

    def set_ip(self, ip):
        self.ip = ip
        self.set_server_address('tcp://' + self.ip + ':' + str(self.port))

    def get_server_address(self):
        return self.server_address

    def set_server_address(self, server_address):
        self.server_address = server_address


def main(top_block_cls=tan_rx_zmq, options=None):

    tb = top_block_cls()
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
