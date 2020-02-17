#!/usr/bin/env python3

from collections import defaultdict

# This is the Network Distributed Database (NDB) interface. 
# If we change from memory (as now) to storage database, just this class need modifications.
class ndb:
	# topology need to be retrieved everytime from SDN controller (because it changes on-the-fly)
    topology = defaultdict(dict)
    # latency metrics
    link_latency = defaultdict(dict)
    # throughput metrics
    link_throughput = defaultdict(dict)
    # known networks
    networks = {}
    # applied routes
    routes = {}

    def get_topology(self):
        return self.topology

    def set_topology(self, topology):
        self.topology = topology

    def new_link(self, src, dst, port):
        self.topology[src][dst] = port

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

