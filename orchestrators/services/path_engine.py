#!/usr/bin/env python3

from services.ndb import ndb
from collections import defaultdict


class PathEngine():

    def get_path(self, topology, src, dst, requirements):
        catalog = ndb()
        catalog.init_arrays()
        print('flows', catalog.get_flows())
        print('usage', catalog.get_usage())
        paths = self.get_paths(topology, src, dst)
        path = self.get_capable_path(paths, requirements)
        return path

    def get_capable_path(self, paths, requirements):
        catalog = ndb()
        throughput = 0
        if requirements is not None:
            # If our platform can support other QoS in the future, please add them as 'if' below:
            if requirements.get('latency') is not None:
                paths = self.get_latency_comply_paths(paths, requirements.get('latency'))
            if requirements.get('throughput') is not None:
                throughput = requirements.get('throughput')
                path = self.get_throughput_comply_path(paths, throughput)
            else:
                if len(paths) > 0:
                    path = min(paths, key=len)
                else:
                    path = None
        if path is not None:
            for p in range(0, len(path) - 1):
                catalog.add_link_usage(path[p], path[p + 1], throughput)
                catalog.add_flow_count(path[p], path[p + 1], 1)
        return path

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
    '''
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
    '''

    def get_throughput_comply_path(self, paths, throughput):
        catalog = ndb()
        flows = catalog.get_flows()
        usage = catalog.get_usage()
        capacity = catalog.get_capacity()
        
        count = {}
        comply_paths = []
        for path in paths:
            is_comply = True
            path_string = ''.join(map(str, path))
            for p in range(0, len(path) - 1):
                if path_string not in count:
                    count[path_string] = 0
                count[path_string] = count[path_string] + flows[path[p]][path[p + 1]]
                if usage[path[p]][path[p + 1]] + throughput >= capacity[path[p]][path[p + 1]]:
                    is_comply = False
                    break
            if is_comply:
                comply_paths.append(path)

        path_to_apply = None
        min_count = 999999999
        if len(comply_paths) > 0:
            print('comply', comply_paths)
            for path in comply_paths:
                path_string = ''.join(map(str, path))
                print(path_string)
                print(min_count)
                print(count[path_string])
                if count[path_string] < min_count:
                    min_count = count[path_string]
                    path_to_apply = path
        return path_to_apply

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
