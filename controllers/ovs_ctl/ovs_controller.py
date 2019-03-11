# Hack to load parent module
from sys import path

# Import the Template Controller
from base_controller import base_controller
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal

import argparse

from ryu.lib import hub
hub.patch()

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp 
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types

def cls():
    system('cls' if name == 'nt' else 'clear')

class ovs_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting OVS Controller')

        self.ovs = kwargs.get('ovs')

        cls()

        # Hold information about the slices
        self.slice_list = {} 

    def pre_exit(self):
     # Terminate the OVS SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        tech = kwargs.get('type', 'high-throughput')
        s_id = kwargs.get('s_id', None)
        destination = kwargs.get('destination', None)

        # Check for validity of the slice ID
        if s_id in self.slice_list:
            return False, 'Slice ID already exists'
        # Check for validity of the destination
        if not destination:
            return False, 'Missing destation'

        # Get the third octet, to denote the slice
        slice_subnet = destination.split('.')[2]

        # Add the slice to the slice list
        self.slice_list[s_id] = {
                'type': tech,
                'subnet': slice_subnet}

        # Get the route depending on the traffic class
        if tech == 'high-throughput':
            # Route 01: High Throughput
            route = {
                'subnet': '1',
                'switches': {
                    'inbound': {
                        'switch': self.ovs.switches['h00'],                    
                        'in_port': 1,
                        'out_port': 2
                        },
                    'outbound': {
                        'switch': self.ovs.switches['h01'],                    
                        'in_port': 1,
                        'out_port': 2
                        }
                    }
                }
            print('\t', 'Setting High-Throughput Route')


        if tech == 'low-latency':
            # Route 02: Low Latency 
            route = {
                'subnet': '2',
                'switches': [
                    {'type': 'inbound',
                     'datapath': self.ovs.switches['h00'],                    
                     'in_port': 1,
                     'out_port': 3
                     },
                    {'type': 'inbound',
                     'datapath': self.ovs.switches['h02'],                    
                     'in_port': 1,
                     'out_port': 3
                     }
                    ]
                }
            print('\t', 'Setting Low-Latency Route')

        # Iterate over the list of switches
        for switch in route['switches']:
            # Get the datapath
            datapath = switch['datapath']

            # Extract the datapath parameters
            dpid = datapath.id
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # Start outputting all packets to port 1
            match = parser.OFPMatch(
                    eth_type=0x0800,
                    in_port=(switch['in_port']),
                    #  ipv4_src=(
                    #   '10.%s.%s.0' % (route['subnet'], slice_subnet), 
                    #   '255.255.255.0'),
                    ipv4_dst=(
                        '10.%s.%s.0' % (route['subnet'], slice_subnet), 
                        '255.255.255.0'),
                )

            #  for x in datapath.ports:
                #  print(x, datapath.ports[x])

            actions = [parser.OFPActionOutput(switch['out_port'])]

            # Add the flow to the switch
            self.ovs.add_flow(datapath, 10, match, actions)

            # Start outputting all packets to port 1
            match = parser.OFPMatch(
                    eth_type=0x0800,
                    in_port=(switch['out_port']),
                    ipv4_src=(
                     '10.%s.%s.0' % (route['subnet'], slice_subnet),
                     '255.255.255.0'),
                    #  ipv4_dst=(
                        #  '10.%s.%s.0' % (route['subnet'], slice_subnet),
                        #  '255.255.255.0'),
                    )

            actions = [parser.OFPActionOutput(switch['in_port'])]

            # Add the flow to the switch
            self.ovs.add_flow(datapath, 10, match, actions)

        #  print('10.%s.%s.0' % (route['subnet'], slice_subnet))

        # Return host and port -- TODO may drop port entirely
        return True, {'host': destination}


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Check for validity of the slice ID
        if s_id not in self.slice_list:
            return False, 'Slice ID does not exist'

        # Getthe slice to the slice list
        tech = self.slice_list[s_id]['type']
        slice_subnet = self.slice_list[s_id]['subnet']

        # Get the route depending on the traffic class
        if tech == 'high-throughput':
            # Route 01: High Throughput 
            switches = [self.ovs.switch['h00'], self.ovs.switches['h01']]
            route_subnet = 1

        if tech == 'low-latency':
            # Route 02: Low Latency 
            switches = [self.ovs.switches['h00'], self.ovs.switches['h02']]
            route_subnet = 2

        # For each switch in the route
        for switch in switches:
            # Extract the datapath parameters
            dpid = switch.id
            ofproto = switch.ofproto
            parser = switch.ofproto_parser

            match = parser.OFPMatch(
                    eth_type=0x0800,
                    #  ipv4_src=(
                     #  '10.%s.%s.0' % (route_subnet, slice_subnet),
                     #  '255.255.255.0'),
                    ipv4_dst=(
                        '10.%s.%s.0' % (route_subnet, slice_subnet),
                        '255.255.255.0'),
                    )

            # Add the flow to the switch
            self.ovs.del_flow(switch, match)

            match = parser.OFPMatch(
                    eth_type=0x0800,
                    ipv4_src=(
                     '10.%s.%s.0' % (route_subnet, slice_subnet),
                     '255.255.255.0'),
                    #  ipv4_dst=(
                        #  '10.%s.%s.0' % (route_subnet, slice_subnet),
                        #  '255.255.255.0'),
                    )

            # Add the flow to the switch
            self.ovs.del_flow(switch, match)

        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': s_id}


class ovs_ctl(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ovs_ctl, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switches = {}

        self.dpid_to_name = {
            95536754289: 'h00',
            95535344413: 'h01',
            95542363502: 'h02'
        }

        #  Instantiate the OVS SDR Controller
        self.ovs_controller_thread = ovs_controller(
            name='OVS',
            req_header='ovs_req', # Don't modify
            rep_header='ovs_rep', # Don't modify
            create_msg='wdc_crs',
            request_msg='wdc_rrs',
            update_msg='wdc_urs',
            delete_msg='wdc_drs',
            host=kwargs.get('host', '127.0.0.1'),
            port=kwargs.get('port', 3300),
            ovs=self
        )

        # Start the OVS SDR Controller Server
        self.ovs_controller_hub = hub.spawn(self.ovs_controller_thread.run)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # Get the new switch
        datapath = ev.msg.datapath
        # Add the new switch to the container 
        self.switches[self.dpid_to_name[datapath.id]] = datapath

        # Send proactive rules to the switches
        self._base_start(datapath)
        
    def _base_start(self, datapath):
        # Extract the datapath parameters
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Match all
        match = parser.OFPMatch({})
        
        # Delete all the existing flows
        self.del_flow(datapath, match)

        match = parser.OFPMatch()
        # Send and ask what to do to the controller
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]

        # Add the controller flow to the switch
        self.add_flow(datapath, 0, match, actions)

        # Output info message
        print('\t','Configured Switch ', self.dpid_to_name[dpid])

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def del_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
                datapath=datapath,
                match=match,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                command=ofproto.OFPFC_DELETE
            )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath 
        in_port = msg.match['in_port']

        dpid = datapath.id
        ofproto = datapath.ofproto

        pkt = packet.Packet(data=msg.data)

        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return

        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_icmp = pkt.get_protocol(icmp.icmp)

        if not pkt_arp:
            return

        #  self.logger.info("packet in %s %s %s %s",
                #  self.dpid_to_name[dpid],
                #  pkt_ethernet.src,
                #  pkt_ethernet.dst,
                #  in_port)

        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][pkt_ethernet.src] = in_port

        if pkt_ethernet.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][pkt_ethernet.dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        self.provision_paths(
                msg, in_port, pkt_ethernet.src, out_port, pkt_ethernet.dst)

    def provision_paths(self, msg, in_port, src, out_port, dst):
        parser = msg.datapath.ofproto_parser
        ofproto = msg.datapath.ofproto
        actions = [parser.OFPActionOutput(out_port)]

        #  print(self.mac_to_port)

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(
                    eth_type=0x0806, # 0x0806 = ARP packet
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src)

            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(msg.datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(msg.datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=msg.datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        msg.datapath.send_msg(out)



