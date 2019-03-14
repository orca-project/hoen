#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Server Hydra
# Generated: Wed Mar 13 19:49:04 2019
##################################################

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt5 import Qt, QtCore
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import hydra
import sys
import threading
from gnuradio import qtgui


class server_hydra(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Server Hydra")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Server Hydra")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "server_hydra")

        if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
            self.restoreGeometry(self.settings.value("geometry").toByteArray())
        else:
            self.restoreGeometry(self.settings.value("geometry", type=QtCore.QByteArray))

        ##################################################
        # Blocks
        ##################################################
        self.hydra_gr_server_0 = hydra.hydra_gr_server("127.0.0.1:5000")
        if 3.75e9 > 0 and 2e6 > 0 and 1024 > 0:
           self.hydra_gr_server_0.set_tx_config(3.75e9, 2e6, 1024, "USRP")
        if 3.75e9 > 0 and 2e6 > 0 and 1024 > 0:
           self.hydra_gr_server_0.set_rx_config(3.75e9, 2e6, 1024, "USRP")
        self.hydra_gr_server_0_thread = threading.Thread(target=self.hydra_gr_server_0.start_server)
        self.hydra_gr_server_0_thread.daemon = True
        self.hydra_gr_server_0_thread.start()

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "server_hydra")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()


def main(top_block_cls=server_hydra, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
