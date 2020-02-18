#!/usr/bin/env python3

from threading import Thread, Lock, Event
from time import sleep
import time
from sonar.log import get_log

logger = get_log('sonar-scoe')

class scoe(Thread):

    def __init__(self, interval=10):
        self.interval = interval
        Thread.__init__(self)
        self.shutdown_flag = Event()
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            logger.info('SCOE should collect now...')
            time.sleep(self.interval)