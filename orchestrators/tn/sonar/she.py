#!/usr/bin/env python3

# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
from time import time

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

        self.historic = {}
        self.shutdown_flag = Event()

    def run(self):
        print('- Started SONAr - Self-Healing Entity')
        # Run while thread is active

        broker = nem()
        while not self.shutdown_flag.is_set():
            metrics = broker.pop_all_metric()
            for metric in metrics:
                self.analyze_paths(metric)
            sleep(0.0001)

    def analyze_paths(self, metric):
        _time = time()
        catalog = ndb()
        routes = catalog.get_routes()
        path_string = catalog.get_virtual_iface(metric.get('src') + '-' + metric.get('dst'))
        self.save(metric, path_string)
        current_latency = float(metric.get('params').get('max'))
        affected_slices = [
            i for i in routes if routes[i].get('path_string') == path_string 
            and routes[i].get('latency') is not None 
            and (routes[i].get('latency') <= current_latency 
                or current_latency < 0)
        ]

        # for prediction:
        pred_latency = self.predict(path_string)
        if pred_latency is not None:
            pred_slices = [
                i for i in routes if routes[i].get('path_string') == path_string 
                and routes[i].get('latency') is not None 
                and (routes[i].get('latency') <= current_latency + pred_latency)
            ]
            affected_slices = affected_slices + pred_slices
        # for buckets evaluation:
        '''
        if len(affected_slices) > 0:
            (bucket_min, bucket_max) = self.get_bucket(current_latency)
            bucket_slices = [
                i for i in routes if routes[i].get('path_string') == path_string 
                and routes[i].get('latency') is not None 
                and (routes[i].get('latency') > current_latency
                    and routes[i].get('latency') <= bucket_max)
            ]
            affected_slices = affected_slices + bucket_slices
        '''
        print('analyze time', time() - _time)
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

    def get_bucket(self, latency):
        if latency < 1:
            return 0, 1
        elif latency < 10:
            return 1, 10
        elif latency < 30:
            return 10, 30
        elif latency < 50:
            return 30, 50
        elif latency < 70:
            return 50, 70
        elif latency < 100:
            return 70, 100
        else:
            return 100, 99999

    def save(self, metric, path_string):
        if path_string not in self.historic.keys():
            self.historic[path_string] = []
        self.historic[path_string].append(metric)

    def predict(self, path_string):
        if len(self.historic[path_string]) < 5:
            return None
        size = len(self.historic[path_string])
        i_metric = self.historic[path_string][size - 5]
        f_metric = self.historic[path_string][size - 1]
        max_diff = float(f_metric.get('params').get('max')) - float(i_metric.get('params').get('max'))
        time_diff = float(f_metric.get('timestamp')) - float(i_metric.get('timestamp'))
        print('max_diff', max_diff, 'time_diff', time_diff)
        if max_diff > 0:
            return max_diff
        else:
            return None

