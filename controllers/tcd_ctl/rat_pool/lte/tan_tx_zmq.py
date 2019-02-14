#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tan Tx Zmq
# Generated: Tue Feb 12 16:24:36 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser


class tan_tx_zmq(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tan Tx Zmq")

        ##################################################
        # Variables
        ##################################################
        self.port = port = 2201
        self.ip = ip = '127.0.0.1'
        self.server_address = server_address = 'tcp://' + ip + ':' + str(port)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1, server_address, 100, False, -1)
        self.digital_ofdm_tx_0 = digital.ofdm_tx(
        	  fft_len=64, cp_len=16,
        	  packet_length_tag_key="len",
        	  bps_header=1,
        	  bps_payload=1,
        	  rolloff=0,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.blocks_tuntap_pdu_1 = blocks.tuntap_pdu('tap0', 1000, True)
        (self.blocks_tuntap_pdu_1).set_max_output_buffer(100000)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, "len")
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.06, ))

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tuntap_pdu_1, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))

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


def main(top_block_cls=tan_tx_zmq, options=None):

    tb = top_block_cls()
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
