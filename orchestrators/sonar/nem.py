#!/usr/bin/env python3

class nem:

    metric_queue = []

    def pop_metric(self):
        if len(self.metric_queue) > 0:
            return self.metric_queue.pop(0)

    def insert_metric(self, metric):
        self.metric_queue.append(metric)

    def pop_all_metric(self):
	    r, self.metric_queue[:] = self.metric_queue[:], []
	    return r