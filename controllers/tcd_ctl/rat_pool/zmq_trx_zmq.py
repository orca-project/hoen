#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Zmq Trx Zmq
# Generated: Tue Feb 12 16:11:59 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser


class zmq_trx_zmq(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Zmq Trx Zmq")

        ##################################################
        # Variables
        ##################################################
        self.tx_source_suffix = tx_source_suffix = 200
        self.tx_destination_suffix = tx_destination_suffix = 201
        self.rx_source_suffix = rx_source_suffix = 501
        self.rx_destination_suffix = rx_destination_suffix = 500
        self.rat_id = rat_id = 2
        self.tx_source_port = tx_source_port = (rat_id * 1000) + tx_source_suffix
        self.tx_destination_port = tx_destination_port = (rat_id * 1000) + tx_destination_suffix
        self.source_ip = source_ip = '127.0.0.1'
        self.rx_source_port = rx_source_port = (rat_id * 1000) + rx_source_suffix
        self.rx_destination_port = rx_destination_port = (rat_id * 1000) + rx_destination_suffix
        self.destination_ip = destination_ip = '127.0.0.1'
        self.tx_source_address = tx_source_address = 'tcp://' + source_ip + ':' + str(tx_source_port)
        self.tx_destination_address = tx_destination_address = 'tcp://' + destination_ip + ':' + str(tx_destination_port)
        self.rx_source_address = rx_source_address = 'tcp://' + source_ip + ':' + str(rx_source_port)
        self.rx_destination_address = rx_destination_address = 'tcp://' + destination_ip + ':' + str(rx_destination_port)
        self.packet_len = packet_len = 84

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_sink_0_0 = zeromq.push_sink(gr.sizeof_char, 1, rx_destination_address, 100, False, -1)
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1, tx_destination_address, 100, True, -1)
        self.zeromq_pull_source_0_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1, rx_source_address, 100, True, -1)
        self.zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_char, 1, tx_source_address, 100, True, -1)
        self.digital_ofdm_tx_0 = digital.ofdm_tx(
        	  fft_len=64, cp_len=16,
        	  packet_length_tag_key='packet_len_tag',
        	  bps_header=1,
        	  bps_payload=1,
        	  rolloff=0,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.digital_ofdm_rx_0 = digital.ofdm_rx(
        	  fft_len=64, cp_len=16,
        	  frame_length_tag_key='frame_'+'rx_len',
        	  packet_length_tag_key='rx_len',
        	  bps_header=1,
        	  bps_payload=1,
        	  debug_log=False,
        	  scramble_bits=False
        	 )
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, packet_len, 'packet_len_tag')
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.06, ))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.digital_ofdm_tx_0, 0))
        self.connect((self.digital_ofdm_rx_0, 0), (self.zeromq_push_sink_0_0, 0))
        self.connect((self.digital_ofdm_tx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.zeromq_pull_source_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.zeromq_pull_source_0_0, 0), (self.digital_ofdm_rx_0, 0))

    def get_tx_source_suffix(self):
        return self.tx_source_suffix

    def set_tx_source_suffix(self, tx_source_suffix):
        self.tx_source_suffix = tx_source_suffix
        self.set_tx_source_port((self.rat_id * 1000) + self.tx_source_suffix)

    def get_tx_destination_suffix(self):
        return self.tx_destination_suffix

    def set_tx_destination_suffix(self, tx_destination_suffix):
        self.tx_destination_suffix = tx_destination_suffix
        self.set_tx_destination_port((self.rat_id * 1000) + self.tx_destination_suffix)

    def get_rx_source_suffix(self):
        return self.rx_source_suffix

    def set_rx_source_suffix(self, rx_source_suffix):
        self.rx_source_suffix = rx_source_suffix
        self.set_rx_source_port((self.rat_id * 1000) + self.rx_source_suffix)

    def get_rx_destination_suffix(self):
        return self.rx_destination_suffix

    def set_rx_destination_suffix(self, rx_destination_suffix):
        self.rx_destination_suffix = rx_destination_suffix
        self.set_rx_destination_port((self.rat_id * 1000) + self.rx_destination_suffix)

    def get_rat_id(self):
        return self.rat_id

    def set_rat_id(self, rat_id):
        self.rat_id = rat_id
        self.set_tx_source_port((self.rat_id * 1000) + self.tx_source_suffix)
        self.set_tx_destination_port((self.rat_id * 1000) + self.tx_destination_suffix)
        self.set_rx_source_port((self.rat_id * 1000) + self.rx_source_suffix)
        self.set_rx_destination_port((self.rat_id * 1000) + self.rx_destination_suffix)

    def get_tx_source_port(self):
        return self.tx_source_port

    def set_tx_source_port(self, tx_source_port):
        self.tx_source_port = tx_source_port
        self.set_tx_source_address('tcp://' + self.source_ip + ':' + str(self.tx_source_port))

    def get_tx_destination_port(self):
        return self.tx_destination_port

    def set_tx_destination_port(self, tx_destination_port):
        self.tx_destination_port = tx_destination_port
        self.set_tx_destination_address('tcp://' + self.destination_ip + ':' + str(self.tx_destination_port))

    def get_source_ip(self):
        return self.source_ip

    def set_source_ip(self, source_ip):
        self.source_ip = source_ip
        self.set_tx_source_address('tcp://' + self.source_ip + ':' + str(self.tx_source_port))
        self.set_rx_source_address('tcp://' + self.source_ip + ':' + str(self.rx_source_port))

    def get_rx_source_port(self):
        return self.rx_source_port

    def set_rx_source_port(self, rx_source_port):
        self.rx_source_port = rx_source_port
        self.set_rx_source_address('tcp://' + self.source_ip + ':' + str(self.rx_source_port))

    def get_rx_destination_port(self):
        return self.rx_destination_port

    def set_rx_destination_port(self, rx_destination_port):
        self.rx_destination_port = rx_destination_port
        self.set_rx_destination_address('tcp://' + self.destination_ip + ':' + str(self.rx_destination_port))

    def get_destination_ip(self):
        return self.destination_ip

    def set_destination_ip(self, destination_ip):
        self.destination_ip = destination_ip
        self.set_tx_destination_address('tcp://' + self.destination_ip + ':' + str(self.tx_destination_port))
        self.set_rx_destination_address('tcp://' + self.destination_ip + ':' + str(self.rx_destination_port))

    def get_tx_source_address(self):
        return self.tx_source_address

    def set_tx_source_address(self, tx_source_address):
        self.tx_source_address = tx_source_address

    def get_tx_destination_address(self):
        return self.tx_destination_address

    def set_tx_destination_address(self, tx_destination_address):
        self.tx_destination_address = tx_destination_address

    def get_rx_source_address(self):
        return self.rx_source_address

    def set_rx_source_address(self, rx_source_address):
        self.rx_source_address = rx_source_address

    def get_rx_destination_address(self):
        return self.rx_destination_address

    def set_rx_destination_address(self, rx_destination_address):
        self.rx_destination_address = rx_destination_address

    def get_packet_len(self):
        return self.packet_len

    def set_packet_len(self, packet_len):
        self.packet_len = packet_len
        self.blocks_stream_to_tagged_stream_0.set_packet_len(self.packet_len)
        self.blocks_stream_to_tagged_stream_0.set_packet_len_pmt(self.packet_len)


def main(top_block_cls=zmq_trx_zmq, options=None):

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
