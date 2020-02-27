#!/usr/bin/env python3

# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep

# Import SONAr modules
from sonar.log import get_log
from sonar.nem import nem
from services.ndb import ndb

logger = get_log('sonar-she')

class she(Thread):

    def __init__(self, orch):
        Thread.__init__(self)
        self.orch = orch
        self.lock = []

        self.shutdown_flag = Event()

    def run(self):
        print('- Started SONAr - Self-Healing Entity')
        # Run while thread is active

        broker = nem()
        while not self.shutdown_flag.is_set():
            metrics = broker.pop_all_metric()
            for metric in metrics:
                self.analyze_paths(metric)
            sleep(0.5)

    def analyze_paths(self, metric):
        catalog = ndb()
        routes = catalog.get_routes()
        path_string = catalog.get_virtual_iface(metric.get('src') + '-' + metric.get('dst'))
        current_latency = float(metric.get('params').get('max'))
        affected_slices = [
            i for i in routes if routes[i].get('path_string') == path_string 
            and routes[i].get('latency') is not None 
            and (routes[i].get('latency') <= current_latency 
                or current_latency < 0)
        ]
        for s_id in affected_slices:
            print('\t', 'SHE - starting reconfiguration of slice ', s_id)
            if s_id not in self.lock:
                try:
                    self.lock.append(s_id)
                    success, msg = self.orch.reconfigure_slice(**{'s_id': s_id})
                    if success:
                        print('\t', 'SHE - reconfiguration finished for ', s_id)
                    else:
                        print('\t', 'SHE - ERROR ', s_id)
                    self.lock.remove(s_id)
                except Exception as e:
                    self.lock.remove(s_id)
                    print('\t', 'SHE - ERROR reconfiguring ', s_id, e)
                    #traceback.print_stack()