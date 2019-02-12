#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tun Tap
# Generated: Tue Feb 12 15:52:56 2019
##################################################


from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser


class tun_tap(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tun Tap")

        ##################################################
        # Variables
        ##################################################
        self.tx_suffix = tx_suffix = 200
        self.rx_suffix = rx_suffix = 500
        self.rat_id = rat_id = 2
        self.tx_port = tx_port = (rat_id * 1000) + tx_suffix
        self.rx_port = rx_port = (rat_id * 1000) + rx_suffix
        self.ip = ip = '127.0.0.1'
        self.tx_address = tx_address = 'tcp://' + ip + ':' + str(tx_port)
        self.rx_address = rx_address = 'tcp://' + ip + ':' + str(rx_port)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_char, 1, rx_address, 100, True, -1)
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_char, 1, tx_address, 100, True, -1)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap' + str(rat_id), 1000, True)
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, '84')

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))

    def get_tx_suffix(self):
        return self.tx_suffix

    def set_tx_suffix(self, tx_suffix):
        self.tx_suffix = tx_suffix
        self.set_tx_port((self.rat_id * 1000) + self.tx_suffix)

    def get_rx_suffix(self):
        return self.rx_suffix

    def set_rx_suffix(self, rx_suffix):
        self.rx_suffix = rx_suffix
        self.set_rx_port((self.rat_id * 1000) + self.rx_suffix)

    def get_rat_id(self):
        return self.rat_id

    def set_rat_id(self, rat_id):
        self.rat_id = rat_id
        self.set_tx_port((self.rat_id * 1000) + self.tx_suffix)
        self.set_rx_port((self.rat_id * 1000) + self.rx_suffix)

    def get_tx_port(self):
        return self.tx_port

    def set_tx_port(self, tx_port):
        self.tx_port = tx_port
        self.set_tx_address('tcp://' + self.ip + ':' + str(self.tx_port))

    def get_rx_port(self):
        return self.rx_port

    def set_rx_port(self, rx_port):
        self.rx_port = rx_port
        self.set_rx_address('tcp://' + self.ip + ':' + str(self.rx_port))

    def get_ip(self):
        return self.ip

    def set_ip(self, ip):
        self.ip = ip
        self.set_tx_address('tcp://' + self.ip + ':' + str(self.tx_port))
        self.set_rx_address('tcp://' + self.ip + ':' + str(self.rx_port))

    def get_tx_address(self):
        return self.tx_address

    def set_tx_address(self, tx_address):
        self.tx_address = tx_address

    def get_rx_address(self):
        return self.rx_address

    def set_rx_address(self, rx_address):
        self.rx_address = rx_address


def main(top_block_cls=tun_tap, options=None):

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
