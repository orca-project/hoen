#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Zmq Usrp Source
# Generated: Thu Nov 29 07:36:32 2018
##################################################


from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time


class zmq_usrp_source(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Zmq Usrp Source")

        ##################################################
        # Variables
        ##################################################
        self.port = port = 6000
        self.ip = ip = '127.0.0.1'
        self.usrp_address = usrp_address = '192.168.0.2'
        self.server_address = server_address = 'udp://' + ip + ':' + str(port)
        self.samp_rate = samp_rate = 1e6
        self.gain = gain = 1
        self.centre_freq = centre_freq = 2e9

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1, server_address, 100, False, -1)
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join((usrp_address, "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(centre_freq, 0)
        self.uhd_usrp_source_0.set_normalized_gain(gain, 0)
        self.uhd_usrp_source_0.set_antenna('RX2', 0)
        self.uhd_usrp_source_0.set_bandwidth(samp_rate, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.zeromq_push_sink_0, 0))

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port
        self.set_server_address('udp://' + self.ip + ':' + str(self.port))

    def get_ip(self):
        return self.ip

    def set_ip(self, ip):
        self.ip = ip
        self.set_server_address('udp://' + self.ip + ':' + str(self.port))

    def get_usrp_address(self):
        return self.usrp_address

    def set_usrp_address(self, usrp_address):
        self.usrp_address = usrp_address

    def get_server_address(self):
        return self.server_address

    def set_server_address(self, server_address):
        self.server_address = server_address

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_bandwidth(self.samp_rate, 0)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_source_0.set_normalized_gain(self.gain, 0)


    def get_centre_freq(self):
        return self.centre_freq

    def set_centre_freq(self, centre_freq):
        self.centre_freq = centre_freq
        self.uhd_usrp_source_0.set_center_freq(self.centre_freq, 0)


def main(top_block_cls=zmq_usrp_source, options=None):

    tb = top_block_cls()
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
