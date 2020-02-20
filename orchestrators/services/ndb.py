#!/usr/bin/env python3

from collections import defaultdict

# This is the Network Distributed Database (NDB) interface. 
# If we change from memory (as now) to storage database, just this class need modifications.
class ndb:
	# topology need to be retrieved everytime from SDN controller (because it changes on-the-fly)
    topology = defaultdict(dict)
    # link capacity should be retrieved from SONAr
    capacity = defaultdict(dict)
    # latency metrics
    link_latency = defaultdict(dict)
    # throughput metrics
    link_throughput = defaultdict(dict)
    # known networks
    networks = {}
    # applied routes
    routes = {}
    # number of current flows per link
    flows = {}
    # number of each link usage
    usage = {}

    def init_arrays(self):
        for src in self.topology:
            if src not in self.flows:
                self.flows[src] = {}
            if src not in self.usage:
                self.usage[src] = {}
            for dst in self.topology[src]:
                if dst not in self.flows[src]:
                    self.flows[src][dst] = 0
                if dst not in self.usage[src]:
                    self.usage[src][dst] = 0

    def get_topology(self):
        return self.topology

    def set_topology(self, topology):
        for src in topology:
            if src not in self.topology:
                self.topology[src] = {}
            for dst in topology[src]:
                if dst not in self.topology[src]:
                    self.topology[src][dst] = topology[src][dst]

    def new_link(self, src, dst, port):
        self.topology[src][dst] = port

    def get_capacity(self):
        return self.capacity

    def set_capacity(self, capacity):
        self.capacity = capacity

    def set_link_capacity(self, src, dst, value):
        self.capacity[src][dst] = value

    def get_link_latency(self):
        return self.link_latency

    def set_link_latency(self, src, dst, latency):
        self.link_latency[src][dst] = latency

    def get_link_throughput(self):
        return self.link_throughput

    def set_link_throughput(self, src, dst, throughput):
        self.link_throughput[src][dst] = throughput

    def get_routes(self):
        return self.routes

    def get_route(self, s_id):
        if s_id not in self.routes.keys():
    	    return None
        return self.routes[s_id]

    def add_route(self, s_id, route):
        self.routes[s_id] = route

    def remove_route(self, s_id):
    	if s_id in self.routes.keys():
    	    del self.routes[s_id]

    def get_networks(self):
        return self.networks

    def get_network(self, network):
    	if network not in self.networks.keys():
    		return None
    	return self.networks[network]

    def add_network(self, network, switch, port):
        self.networks[network] = { 'switch': switch, 'port': port }

    def remove_network(self, network):
        del self.networks[network]

    def get_usage(self):
        return self.usage

    def add_link_usage(self, src, dst, value):
        if src not in self.usage:
            self.usage[src] = {}
        if dst not in self.usage[src]:
            self.usage[src][dst] = 0
        self.usage[src][dst] = self.usage[src][dst] + value

    def get_flows(self):
        return self.flows

    def add_flow_count(self, src, dst, count):
        if src not in self.flows:
            self.flows[src] = {}
        if dst not in self.flows[src]:
            self.flows[src][dst] = 0
        self.flows[src][dst] = self.flows[src][dst] + count