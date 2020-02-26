#!/usr/bin/env python3

from collections import defaultdict

# This is the Network Distributed Database (NDB) interface. 
# If we change from memory (as now) to storage database, just this class need modifications.
class ndb:
	# topology need to be retrieved everytime from SDN controller (because it changes on-the-fly)
    topology = defaultdict(dict)
    # link capacity should be retrieved from SONAr
    capacity = defaultdict(dict)
    # known networks
    networks = {}
    # applied routes
    routes = {}
    # number of current flows per link
    flows = {}
    # number of each link usage
    usage = {}
    # local agents used by SONAr to collect metrics
    local_agents = {}
    # agents already configured by SONAr
    configured_agents = {}
    # latency of each path sent by the SONAr local agents
    path_latency = {}
    # virtual interface addresses configured in the local agents
    virtual_ifaces = {}

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

    def add_local_agent(self, name, host, iface, switch, port):
        agent = { 
                    'name': name,
                    'host': host,
                    'management_iface': iface,
                    'switch': switch,
                    'port': port
                }
        self.local_agents[name] = agent
        return agent

    def get_local_agents(self):
        return self.local_agents

    def get_local_agent(self, name):
        if name not in self.local_agents.keys():
            return None
        return self.local_agents[name]

    def get_configured_agents(self):
        return self.configured_agents

    def get_connfigured_agent(self, name):
        if name not in self.configured_agents.keys():
            return None
        return self.configured_agents[name]

    def add_configured_agent(self, name, src, dst):
        configured_agent = { 
                    'name': name,
                    'src': src,
                    'dst': dst
                }
        self.configured_agents['name'] = configured_agent
        return configured_agent

    def get_path_latencies(self):
        return self.path_latency

    def set_path_latency(self, path, params):
        self.path_latency[path] = params

    def get_path_latency(self, path):
        if path not in self.path_latency.keys():
            return None
        return self.path_latency[path]

    def get_virtual_ifaces(self):
        return self.virtual_ifaces

    def get_virtual_iface(self, addresses):
        if addresses not in self.virtual_ifaces.keys():
            return None
        return self.virtual_ifaces[addresses]

    def add_virtual_iface(self, addresses, path):
        self.virtual_ifaces[addresses] = path