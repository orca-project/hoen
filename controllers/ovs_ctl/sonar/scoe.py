#!/usr/bin/env python3

from threading import Thread, Lock, Event
from time import sleep
import time
from sonar.log import get_log


import logging
import json
import ast

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.exception import RyuException
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_4
from ryu.ofproto import ofproto_v1_5
from ryu.lib import ofctl_v1_0
from ryu.lib import ofctl_v1_2
from ryu.lib import ofctl_v1_3
from ryu.lib import ofctl_v1_4
from ryu.lib import ofctl_v1_5
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import WSGIApplication

logger = get_log('sonar-scoe')

supported_ofctl = {
    ofproto_v1_0.OFP_VERSION: ofctl_v1_0,
    ofproto_v1_2.OFP_VERSION: ofctl_v1_2,
    ofproto_v1_3.OFP_VERSION: ofctl_v1_3,
    ofproto_v1_4.OFP_VERSION: ofctl_v1_4,
    ofproto_v1_5.OFP_VERSION: ofctl_v1_5,
}

class scoe(Thread):

    def __init__(self, ovs, interval=60):
        self.ovs = ovs
        self.interval = interval
        Thread.__init__(self)
        self.shutdown_flag = Event()
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            try:
                for dpid in self.ovs.dpid_to_name:
                    node = self.ovs.dpid_to_name.get(dpid)
                    dp = self.ovs.switches[node]
                    ofctl = supported_ofctl.get(dp.ofproto.OFP_VERSION)
                    stats = ofctl.get_port_stats(dp, self.ovs.waiters)
                    #logger.info(stats)
                    desc = ofctl.get_port_desc(dp, self.ovs.waiters)
                    logger.info(desc)
            except Exception as e: 
                logger.error(e)
                pass
            time.sleep(self.interval)