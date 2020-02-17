#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Orchestrator
from base_orchestrator.base_orchestrator import base_orchestrator, ctl_base
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal
from time import time

# Import SONAr services
from services.ndb import ndb
from services.path_engine import PathEngine

def cls():
    system('cls' if name=='nt' else 'clear')

class ovs_base(ctl_base):
    def post_init(self, **kwargs):

        self.topology_msg = kwargs.get("topology_msg", "ctl_ts")
        self.topology_ack = "_".join([self.topology_msg.split('_')[-1], "ack"])
        self.topology_nack = "_".join([self.topology_msg.split('_')[-1], "nack"])

    def get_topology(self, **kwargs):
        # Send request message
        success, msg = self._send_msg(
            self.topology_ack, self.topology_nack, **{self.topology_msg: kwargs})

        # If the slice request failed
        if not success:
            # Inform the hyperstrator about the failure
            self._log('Failed requesting a ' + self.type + \
                      ' topology in ' + self.name)
            return False, msg

        # Otherwise, it succeeded
        else:
            # Inform the hyperstrator about the success
            self._log('Succeeded requesting a ' + self.type + \
                      ' topology in ' + self.name)
            return True, msg

        return msg


class tn_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # OVS Controller Handler
        self.ovs_ctl = ovs_base(
            name="OVS",
            host_key="ovs_host",
            port_key="ovs_port",
            default_host="127.0.0.1",
            default_port="3200",
            request_key="ovs_req",
            reply_key="ovs_rep",
            create_msg='ovc_crs',
            request_msg='ovc_rrs',
            update_msg='ovc_urs',
            delete_msg='ovc_drs',
            topology_msg='ovc_trs')

        # setting metrics manually
        # TODO: to create a service to fetch these metrics automatically from ovsdb or ofconfig
        catalog = ndb()
        catalog.set_link_latency('h00','h01', 0.1)
        catalog.set_link_latency('h01', 'h00', 0.1)
        catalog.set_link_latency('h00', 'h02', 0.1)
        catalog.set_link_latency('h02', 'h00', 0.1)
        catalog.set_link_latency('h00', 'h03', 0.1)
        catalog.set_link_latency('h03', 'h00', 0.1)
        catalog.set_link_latency('h02', 'h03', 0.1)
        catalog.set_link_latency('h03', 'h02', 0.1)
        catalog.set_link_throughput('h00', 'h01', 10)
        catalog.set_link_throughput('h01', 'h00', 10)
        catalog.set_link_throughput('h00', 'h02', 10)
        catalog.set_link_throughput('h02', 'h00', 10)
        catalog.set_link_throughput('h00', 'h03', 10)
        catalog.set_link_throughput('h03', 'h00', 10)
        catalog.set_link_throughput('h02', 'h03', 10)
        catalog.set_link_throughput('h03', 'h02', 10)

        '''
        Setting known hosts and networks manually.
        It could be automatic if we develop LLDP and ARP functions in the ovs controller...
        ... but it is out of scope.
        '''
        catalog.add_network('10.0.0.4', 'h00', 1)
        catalog.add_network('10.1.0.1', 'h01', 2)
        catalog.add_network('10.2.0.1', 'h02', 3)


    def create_slice(self, **kwargs):
        catalog = ndb()
        st = time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        source = kwargs.get('source', None)
        destination = kwargs.get('destination', None)
        qos = kwargs.get('requirements', None)

        # Append it to the list of service IDs
        self.s_ids[s_id] = qos

        # Get network topology
        (topo_success, topo_msg) = self.ovs_ctl.get_topology()
        if not topo_success:
            # Send error message
            msg = '[ERROR]: Could not retrieve the network topology from ovs controller'
            print('failed', (time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        topology = topo_msg.get('topology')

        # Define the route which can support the required QoS
        route = self.build_route(topology, source, destination, qos)

        if route is None:
            # Send error message
            msg = '[WARN]: There is no available path for source '+  str(source) + ' and destination ' + str(destination) + ' supporting the follow QoS: ' + str(qos)
            print('failed', (time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        # Send message to OVS SDN controller
        self._log('Delegating it to the OVS Controller')

        # Send the message to create a slice
        success, msg = self.ovs_ctl.create_slice(
                **{'s_id': s_id,
                    'destination': kwargs.get('destination'),
                    'route': route
                    })

        print('success', (time()-st)*1000, 'ms')

        if success:
            catalog.add_route(s_id, route)
        # Inform the user about the creation
        return success, msg

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Retrieve the route previously applied
        catalog = ndb()
        route = catalog.get_route(s_id)

        if route is None:
            return False, 'Route not found for s_id ' + s_id

        # Send message to remove slice
        success, msg = self.ovs_ctl.delete_slice(**{'s_id': s_id,
                                                    'route': route})

        if success:
            catalog.remove_route(s_id)
        # Inform the user about the removal
        return success, msg

    def build_route(self, topology, src, dst, qos):
        catalog = ndb()
        catalog.set_topology(topology)
        engine = PathEngine()

        # Fetch switches which can arrive to the src and dst networks
        src_network = catalog.get_network(src)
        dst_network = catalog.get_network(dst)

        self._log('Source network: ', src_network)
        self._log('Destination network: ', dst_network)
        if src_network is None or dst_network is None:
            self._log('Impossible to arrive from ', src, 'to ', dst)
            return None

        # Define the path to apply
        path = engine.get_path(topology, src_network.get('switch'), dst_network.get('switch'), qos)
        if path is None:
            return None

        self._log('Path to be applied: ', path)
        (ipv4_src, ipv4_src_netmask) = self.convert_cidr_to_netmask(src)
        (ipv4_dst, ipv4_dst_netmask) = self.convert_cidr_to_netmask(dst)

        first_port = src_network.get('port')
        last_port = dst_network.get('port')
        switches = engine.generate_match_switches(topology, path, first_port, last_port)

        route = {
            'ipv4_src': ipv4_src,
            'ipv4_src_netmask': ipv4_src_netmask,
            'ipv4_dst': ipv4_dst,
            'ipv4_dst_netmask': ipv4_dst_netmask,
            'switches': switches
            }
        return route

    def convert_cidr_to_netmask(self, address):
        if "/" not in address:
            address = address + "/32"
        (ipv4, original_cidr) = address.split('/')
        addr = ipv4.split('.')
        cidr = int(original_cidr)
        mask = [0, 0, 0, 0]
        for i in range(cidr):
            mask[i//8] = mask[i//8] + (1 << (7 - i % 8))
        net = []
        for i in range(4):
            net.append(int(addr[i]) & mask[i])
        ipv4_netmask = ".".join(map(str, mask))
        return (ipv4, ipv4_netmask)

if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Transport Network Orchestrator thread
        tn_orchestrator_thread = tn_orchestrator(
            name='TN',
            req_header='tn_req',
            rep_header='tn_rep',
            error_msg='msg_err',
            create_msg='tn_cc',
            request_msg='tn_rc',
            update_msg='tn_uc',
            delete_msg='tn_dc',
            topology_msg='tn_tc',
            host='127.0.0.1',
            port=2200
        )

        # Start the Transport Network Orchestrator
        tn_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TN Orchestrator Server
        tn_orchestrator_thread.safe_shutdown()
