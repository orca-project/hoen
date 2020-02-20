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
import time 

# Import SONAr services
from services.ndb import ndb
from services.path_engine import PathEngine
# Import SONAr modules
from sonar.scoe import scoe

def cls():
    system('cls' if name=='nt' else 'clear')

class wired_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # IMEC Controller Handler
        self.ovs_ctl = ctl_base(
            name="OVS",
            host_key="ovs_host",
            port_key="ovs_port",
            default_host="10.0.0.5",
            default_port="3300",
            request_key="ovs_req",
            reply_key="ovs_rep",
            create_msg='wdc_crs',
            request_msg='wdc_rrs',
            update_msg='wdc_urs',
            delete_msg='wdc_drs',
            topology_msg='wdc_trs')

        # setting metrics manually
        # TODO: to create a service to fetch these metrics automatically from ovsdb or ofconfig
        catalog = ndb()
        catalog.set_link_latency('s01','s02', 0.1)
        catalog.set_link_latency('s02','s01', 0.1)
        catalog.set_link_latency('s01','s03', 0.1)
        catalog.set_link_latency('s03','s01', 0.1)
        catalog.set_link_latency('s02','s05', 0.1)
        catalog.set_link_latency('s05','s02', 0.1)
        catalog.set_link_latency('s03','s04', 0.1)
        catalog.set_link_latency('s04','s03', 0.1)
        catalog.set_link_latency('s04','s05', 0.1)
        catalog.set_link_latency('s05','s04', 0.1)
        catalog.set_link_throughput('s01','s02', 10)
        catalog.set_link_throughput('s02','s01', 10)
        catalog.set_link_throughput('s01','s03', 10)
        catalog.set_link_throughput('s03','s01', 10)
        catalog.set_link_throughput('s02','s05', 10)
        catalog.set_link_throughput('s05','s02', 10)
        catalog.set_link_throughput('s03','s04', 10)
        catalog.set_link_throughput('s04','s03', 10)
        catalog.set_link_throughput('s04','s05', 10)
        catalog.set_link_throughput('s05','s04', 10)

        catalog.set_link_capacity('s01','s02', 100)
        catalog.set_link_capacity('s02','s01', 100)
        catalog.set_link_capacity('s01','s03', 100)
        catalog.set_link_capacity('s03','s01', 100)
        catalog.set_link_capacity('s02','s05', 100)
        catalog.set_link_capacity('s05','s02', 100)
        catalog.set_link_capacity('s03','s04', 100)
        catalog.set_link_capacity('s04','s03', 100)
        catalog.set_link_capacity('s04','s05', 100)
        catalog.set_link_capacity('s05','s04', 100)

        '''
        Setting known hosts and networks manually.
        It could be automatic if we develop LLDP and ARP functions in the ovs controller...
        ... but it is out of scope.
        '''
        catalog.add_network('10.0.0.4', 's01', 1)
        catalog.add_network('10.0.0.30', 's01', 5)
        catalog.add_network('10.1.0.1', 's05', 3)
        #catalog.add_network('10.2.0.1', 's05', 3)


    def create_slice(self, **kwargs):
        catalog = ndb()
        st = time.time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        source = kwargs.get('source', None)
        destination = kwargs.get('destination', None)
        requirements = kwargs.get('requirements', None)

        # Get network topology
        (topo_success, topo_msg) = self.ovs_ctl.get_topology()    
        if not topo_success:
            # Send error message
            msg = '[ERROR]: Could not retrieve the network topology from ovs controller'
            print('failed', (time.time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        topology = topo_msg.get('topology')
        catalog.set_topology(topology)

        # Define the route which can support the required QoS
        route = self.build_route(topology, source, destination, requirements)

        if route is None:
            # Send error message
            msg = '[WARN]: There is no available path for source '+  str(source) + ' and destination ' + str(destination) + ' supporting the follow QoS: ' + str(requirements)
            print('failed', (time.time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        # Send message to OVS SDN controller
        print('\t', 'Delegating it to the OVS Controller')

        # Send the message to create a slice
        success, msg = self.ovs_ctl.create_slice(
                **{'s_id': s_id,
                    'route': route
                    })

        print('success', (time.time()-st)*1000, 'ms')

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
                                                    #'type': s_type,
                                                    'route': route})

        if success:
            catalog.remove_route(s_id)
        # Inform the user about the removal
        return success, msg

    def build_route(self, topology, src, dst, requirements):
        catalog = ndb()
        engine = PathEngine()

        # Fetch switches which can arrive to the src and dst networks
        src_network = catalog.get_network(src)
        dst_network = catalog.get_network(dst)

        print('\t', 'Source network: ', src_network)
        print('\t', 'Destination network: ', dst_network)
        if src_network is None or dst_network is None:
            print('\t', 'Impossible to arrive from ', src, 'to ', dst)
            return None

        # Define the path to apply
        path = engine.get_path(topology, src_network.get('switch'), dst_network.get('switch'), requirements)
        if path is None:
            return None

        print('\t', 'Path to be applied: ', path)
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
        # Instantiate the Wired Network Orchestrator thread
        wired_orchestrator_thread = wired_orchestrator(
            name='SDN',
            req_header='sdn_req',
            rep_header='sdn_rep',
            error_msg='msg_err',
            create_msg='wd_cc',
            request_msg='wd_rc',
            update_msg='wd_uc',
            delete_msg='wd_dc',
            topology_msg='wd_tc',
            host='10.0.0.2',
            port=2200
        )

        # Start SONAr modules
        # scoe_thread = scoe()

        # Start the Wired Network Orchestrator
        wired_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Wired Orchestrator Server
        print('Exiting')
        wired_orchestrator_thread.shutdown_flag.set()
        wired_orchestrator_thread.join()
