#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Zmq Usrp Both
# Generated: Wed Mar  6 04:32:35 2019
##################################################


from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import zeromq
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time


class zmq_usrp_both(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Zmq Usrp Both")

        ##################################################
        # Variables
        ##################################################
        self.source_port = source_port = 2201
        self.ip = ip = '127.0.0.1'
        self.destination_port = destination_port = 2501
        self.usrp_address = usrp_address = "serial=30C628B"
        self.source_address = source_address = 'tcp://' + ip + ':' + str(source_port)
        self.samp_rate = samp_rate = 1e6
        self.gain = gain = 1
        self.destination_address = destination_address = 'tcp://' + ip + ':' + str(destination_port)
        self.centre_freq_tx = centre_freq_tx = 2e9-1e6
        self.centre_freq_rx = centre_freq_rx = 2e9+1e6

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_gr_complex, 1, destination_address, 100, True, -1)
        self.zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1, source_address, 100, True, -1)
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join((usrp_address, "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(centre_freq_rx, 0)
        self.uhd_usrp_source_0.set_normalized_gain(gain, 0)
        self.uhd_usrp_source_0.set_antenna('RX2', 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join((usrp_address, "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(centre_freq_tx, 0)
        self.uhd_usrp_sink_0.set_normalized_gain(gain, 0)
        self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.uhd_usrp_source_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.zeromq_pull_source_0, 0), (self.uhd_usrp_sink_0, 0))

    def get_source_port(self):
        return self.source_port

    def set_source_port(self, source_port):
        self.source_port = source_port
        self.set_source_address('tcp://' + self.ip + ':' + str(self.source_port))

    def get_ip(self):
        return self.ip

    def set_ip(self, ip):
        self.ip = ip
        self.set_source_address('tcp://' + self.ip + ':' + str(self.source_port))
        self.set_destination_address('tcp://' + self.ip + ':' + str(self.destination_port))

    def get_destination_port(self):
        return self.destination_port

    def set_destination_port(self, destination_port):
        self.destination_port = destination_port
        self.set_destination_address('tcp://' + self.ip + ':' + str(self.destination_port))

    def get_usrp_address(self):
        return self.usrp_address

    def set_usrp_address(self, usrp_address):
        self.usrp_address = usrp_address

    def get_source_address(self):
        return self.source_address

    def set_source_address(self, source_address):
        self.source_address = source_address

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_source_0.set_normalized_gain(self.gain, 0)

        self.uhd_usrp_sink_0.set_normalized_gain(self.gain, 0)


    def get_destination_address(self):
        return self.destination_address

    def set_destination_address(self, destination_address):
        self.destination_address = destination_address

    def get_centre_freq_tx(self):
        return self.centre_freq_tx

    def set_centre_freq_tx(self, centre_freq_tx):
        self.centre_freq_tx = centre_freq_tx
        self.uhd_usrp_sink_0.set_center_freq(self.centre_freq_tx, 0)

    def get_centre_freq_rx(self):
        return self.centre_freq_rx

    def set_centre_freq_rx(self, centre_freq_rx):
        self.centre_freq_rx = centre_freq_rx
        self.uhd_usrp_source_0.set_center_freq(self.centre_freq_rx, 0)


def main(top_block_cls=zmq_usrp_both, options=None):

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
