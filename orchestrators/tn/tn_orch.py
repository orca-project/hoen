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

from netaddr import IPAddress, IPNetwork

# Import SONAr services
from services.ndb import ndb
from services.path_engine import PathEngine
# Import SONAr modules
from sonar.scoe import scoe
from sonar.she import she
from sonar.nad import nad

def cls():
    system('cls' if name=='nt' else 'clear')

class tn_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # OVS Controller Handler
        self.ovs_ctl = ctl_base(
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

        # setting link speeds manually
        # TODO: to create a service to fetch these values automatically from ovsdb or ofconfig
        catalog = ndb()
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
        catalog.add_network('10.1.0.1/16', 's05', 3)
        #catalog.add_network('10.2.0.1', 's05', 3)

    def create_slice(self, **kwargs):
        catalog = ndb()
        st = time()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        source = kwargs.get('source', None)
        destination = kwargs.get('destination', None)
        requirements = kwargs.get('requirements', None)

        # Append it to the list of service IDs
        self.s_ids[s_id] = requirements

        # Get network topology
        (topo_success, topo_msg) = self.ovs_ctl.get_topology()
        if not topo_success:
            # Send error message
            msg = '[ERROR]: Could not retrieve the network topology from ovs controller'
            print('failed', (time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        topology = topo_msg.get('topology')
        catalog.set_topology(topology)

        # Define the route which can support the required QoS
        route = self.build_route(topology, source, destination, requirements)

        if route is None:
            # Send error message
            msg = '[WARN]: There is no available path for source '+  str(source) + ' and destination ' + str(destination) + ' supporting the follow QoS: ' + str(requirements)
            print('failed', (time()-st)*1000, 'ms')
            # Inform the user about the creation
            return False, msg

        # Send message to OVS SDN controller
        self._log('Delegating it to the OVS Controller')

        # Send the message to create a slice
        success, msg = self.ovs_ctl.create_slice(
                **{'s_id': s_id,
                    'route': route
                    })

        print('success', (time()-st)*1000, 'ms')

        if success:
            catalog.add_route(s_id, route)
        # Inform the user about the creation
        return success, msg

    def request_slice(self, **kwargs):
        pass

    def update_slice(self, **kwargs):
        pass

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        route = kwargs.get('route', None)
        complete_remove = False

        catalog = ndb()
        if route is None:
            # Retrieve the route previously applied
            complete_remove = True            
            route = catalog.get_route(s_id)

            if route is None:
                return False, 'Route not found for s_id ' + s_id

        # Send message to remove slice
        success, msg = self.ovs_ctl.delete_slice(**{'s_id': s_id,
                                                    'route': route})
        if success:
            path = route['path']
            for p in range(0, len(path) - 1):
                catalog.add_flow_count(path[p], path[p + 1], -1)
                if route['throughput'] is not None:
                    catalog.add_link_usage(path[p], path[p + 1], -route['throughput'])
            if complete_remove:
                catalog.remove_route(s_id)
        # Inform the user about the removal
        return success, msg

    # TODO: initial version is using create_slice service. Change it to have its own services.
    def reconfigure_slice(self, **kwargs):
        s_id = kwargs.get('s_id', None)
        catalog = ndb()
        old_route = catalog.get_route(s_id)

        source = old_route.get('src')
        destination = old_route.get('dst')
        latency = old_route.get('latency')
        throughput = old_route.get('throughput')

        slice_args = {'s_id': s_id,
                        'source': source,
                        'destination': destination,
                        'requirements': {'throughput': throughput,
                                      'latency': latency}
                     }
        print('slice args ', slice_args)
        (success, msg) = self.create_slice(**slice_args)
        print('create success ', success)
        if success:
            switches = []
            new_route = catalog.get_route(s_id)
            print('new_route', new_route)
            if old_route.get('path_string') != new_route.get('path_string'):
                for old in old_route.get('switches'):
                    current = self.get_in_switches(old, new_route.get('switches'))
                    if len(current) > 0:
                        #if old.get('in_port') != current[0].get('in_port'):
                        #    switches.append(old)
                        if old.get('in_port') != current[0].get('in_port'):
                            if old.get('out_port') != current[0].get('out_port'):
                                old['direction'] = 'full'
                                switches.append(old)
                            else:
                                old['direction'] = 'half-fw'
                                switches.append(old)
                        elif old.get('out_port') != current[0].get('out_port'):
                            old['direction'] = 'half-rv'
                            switches.append(old)
                    else:
                        old['direction'] = 'full'
                        switches.append(old)
                route_to_delete = self.generate_route_to_delete(old_route, switches)
                success, msg = self.delete_slice(**{'s_id': s_id,
                                                            'route': route_to_delete})
        return success, msg


    def get_in_switches(self, switch, switches):
        return [
            i for i in switches
            if i.get('node') == switch.get('node')
            ]

    def generate_route_to_delete(self, old_route, switches):
        route = old_route
        route['switches'] = switches
        return route

    def find_border_switch(self, address):
        catalog = ndb()
        resp = None
        networks = catalog.get_networks()
        for network in networks:
            if IPAddress(address) in IPNetwork(network):
                resp = networks[network]
                break
        return resp

    def build_route(self, topology, src, dst, requirements):
        catalog = ndb()
        engine = PathEngine()

        # Fetch switches which can arrive to the src and dst networks
        src_network = self.find_border_switch(src)
        dst_network = self.find_border_switch(dst)

        if src_network is None or dst_network is None:
            print('\t', 'Impossible to arrive from ', src, 'to ', dst)
            return None

        # Define the path to apply
        path = engine.get_path(topology, src_network.get('switch'), dst_network.get('switch'), requirements)
        print('path ', path)
        if path is None:
            return None

        print('\t', 'Path to be applied: ', path)
        (ipv4_src, ipv4_src_netmask) = self.convert_cidr_to_netmask(src)
        (ipv4_dst, ipv4_dst_netmask) = self.convert_cidr_to_netmask(dst)
        (min_rate, max_rate, priority) = self.define_queue_parameters(requirements)
        
        first_port = src_network.get('port')
        last_port = dst_network.get('port')
        switches = engine.generate_match_switches(topology, path, first_port, last_port)
        path_string = '-'.join(map(str, path))

        route = {
            'src': src,
            'dst': dst,
            'ipv4_src': ipv4_src,
            'ipv4_src_netmask': ipv4_src_netmask,
            'ipv4_dst': ipv4_dst,
            'ipv4_dst_netmask': ipv4_dst_netmask,
            'min_rate': min_rate,
            'max_rate': max_rate,
            'priority': priority,
            'switches': switches,
            'path_string': path_string,
            'path': path,
            'latency': requirements.get('latency'),
            'throughput': requirements.get('throughput')
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

    def define_queue_parameters(self, requirements):
        min_rate = None
        max_rate = None
        priority = None
        if requirements.get('throughput') is not None:
            min_rate = self.to_byte(requirements.get('throughput'))
            #max_rate = self.to_byte(requirements.get('throughput'))
            priority = 10
        if requirements.get('latency') is not None:
            priority = 1
        return min_rate, max_rate, priority

    def to_byte(self, value):
        return int(value * 1024 * 1024)

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
            host='0.0.0.0',
            port=2200
        )

        # Start the Transport Network Orchestrator
        tn_orchestrator_thread.start()

        # Start SONAr modules
        scoe_thread = scoe(tn_orchestrator_thread, "0.0.0.0", 5500)
        scoe_thread.start()

        she_thread = she(tn_orchestrator_thread)
        she_thread.start()

        api_thread = nad()
        api_thread.start()

        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TN Orchestrator Server
        tn_orchestrator_thread.safe_shutdown()

        scoe_thread.shutdown_flag.set()
        scoe_thread.join()
        she_thread.shutdown_flag.set()
        she_thread.join()
        api_thread.shutdown_flag.set()
        api_thread.join()
