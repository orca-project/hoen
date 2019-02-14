#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tan Trx Zmq
# Generated: Wed Feb 13 23:06:51 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser


class tan_trx_zmq(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tan Trx Zmq")

        ##################################################
        # Variables
        ##################################################
        self.source_suffix = source_suffix = 501
        self.rat_id = rat_id = 2
        self.destination_suffix = destination_suffix = 201
        self.source_port = source_port = (rat_id * 1000) + source_suffix
        self.source_ip = source_ip = '127.0.0.1'
        self.destination_port = destination_port = (rat_id * 1000) + destination_suffix
        self.destination_ip = destination_ip = '127.0.0.1'
        self.source_address = source_address = 'tcp://' + source_ip + ':' + str(source_port)
        self.packet_len = packet_len = 84
        self.destination_address = destination_address = 'tcp://' + destination_ip + ':' + str(destination_port)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1, destination_address, 100, True, -1)
        self.zeromq_pull_source_0_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1, source_address, 100, True, -1)
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
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.06, ))

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.zeromq_pull_source_0_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_source_suffix(self):
        return self.source_suffix

    def set_source_suffix(self, source_suffix):
        self.source_suffix = source_suffix
        self.set_source_port((self.rat_id * 1000) + self.source_suffix)

    def get_rat_id(self):
        return self.rat_id

    def set_rat_id(self, rat_id):
        self.rat_id = rat_id
        self.set_source_port((self.rat_id * 1000) + self.source_suffix)
        self.set_destination_port((self.rat_id * 1000) + self.destination_suffix)

    def get_destination_suffix(self):
        return self.destination_suffix

    def set_destination_suffix(self, destination_suffix):
        self.destination_suffix = destination_suffix
        self.set_destination_port((self.rat_id * 1000) + self.destination_suffix)

    def get_source_port(self):
        return self.source_port

    def set_source_port(self, source_port):
        self.source_port = source_port
        self.set_source_address('tcp://' + self.source_ip + ':' + str(self.source_port))

    def get_source_ip(self):
        return self.source_ip

    def set_source_ip(self, source_ip):
        self.source_ip = source_ip
        self.set_source_address('tcp://' + self.source_ip + ':' + str(self.source_port))

    def get_destination_port(self):
        return self.destination_port

    def set_destination_port(self, destination_port):
        self.destination_port = destination_port
        self.set_destination_address('tcp://' + self.destination_ip + ':' + str(self.destination_port))

    def get_destination_ip(self):
        return self.destination_ip

    def set_destination_ip(self, destination_ip):
        self.destination_ip = destination_ip
        self.set_destination_address('tcp://' + self.destination_ip + ':' + str(self.destination_port))

    def get_source_address(self):
        return self.source_address

    def set_source_address(self, source_address):
        self.source_address = source_address

    def get_packet_len(self):
        return self.packet_len

    def set_packet_len(self, packet_len):
        self.packet_len = packet_len

    def get_destination_address(self):
        return self.destination_address

    def set_destination_address(self, destination_address):
        self.destination_address = destination_address


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
