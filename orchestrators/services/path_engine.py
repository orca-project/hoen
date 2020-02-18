#!/usr/bin/env python3

from services.ndb import ndb
from collections import defaultdict


class PathEngine():

    def get_path(self, topology, src, dst, qos):
        paths = self.get_paths(topology, src, dst)
        paths = self.get_capable_paths(paths, qos)
        if len(paths) > 0:
            return min(paths, key=len)
        return None

    def get_capable_paths(self, paths, qos):
        if qos is not None:
            # If our platform can support other QoS in the future, please add them as 'if' below:
            if qos.get('latency') is not None:
                paths = self.get_latency_comply_paths(paths, qos.get('latency'))
            if qos.get('throughput') is not None:
                paths = self.get_throughput_comply_paths(paths, qos.get('throughput'))
        return paths

    # This function applies the logic for latency QoS. Change it if necessary.
    def get_latency_comply_paths(self, paths, latency):
        catalog = ndb()
        link_latency = catalog.get_link_latency()
        comply_paths = []
        for path in paths:
            sum = 0
            for p in range(0, len(path) - 1):
                sum += link_latency[path[p]][path[p + 1]]
            if sum < latency:
                comply_paths.append(path)
        return comply_paths

    # This function applies the logic for throughput QoS. Change it if necessary.
    def get_throughput_comply_paths(self, paths, throughput):
        catalog = ndb()
        link_latency = catalog.get_link_throughput()
        comply_paths = []
        for path in paths:
            is_comply = True
            for p in range(0, len(path) - 1):
                if link_throughput[path[p]][path[p + 1]] < throughput:
                    is_comply = False
                    break
            if is_comply:
                comply_paths.append(path)
        return comply_paths

    # This function applies a Deep-First Source (DFS) algorithm to find all paths in the graph
    def get_paths(self, topology, src, dst):
        if src == dst:
            return [[src]]
        paths = []
        stack = [(src, [src])]
        while stack:
            (node, path) = stack.pop()
            for next in set(topology[node].keys()) - set(path):
                if next == dst:
                    paths.append(path + [next])
                else:
                    stack.append((next, path + [next]))
        return paths

    # This function creates the list of switches (with input and output ports), which will be applied in the ovs
    def generate_match_switches(self, topology, path, first_port, last_port):
        switches = []
        for p in range(0, len(path)):
            node = path[p]
            if p == 0:
                p_in = first_port
                if len(path) == 1:
                    p_out = last_port
                else:
                    p_out = topology[path[p]][path[p + 1]]
                switches.append(self.append_switch(node, p_in, p_out))
            elif p == len(path) - 1:
                p_in = topology[path[p]][path[p - 1]]
                p_out = last_port
                switches.append(self.append_switch(node, p_in, p_out))
            else:
                p_in = topology[path[p]][path[p - 1]]
                p_out = topology[path[p]][path[p + 1]]
                switches.append(self.append_switch(node, p_in, p_out))
        return switches

    def append_switch(self, node, p_in, p_out):
        switch = {'node': node, 'eth_type': 0x0800, 'in_port': p_in, 'out_port': p_out}
        return switch
