# Hack to load parent module
from sys import path

# Import the Template Controller
from base_controller import base_controller
# Import the System and Name methods from the OS module
from os import system, name
# Import signal
import signal
from time import sleep
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
from ryu.lib.packet import ipv4 
from ryu.lib.packet import arp 
from ryu.lib.packet import ether_types
from ryu.lib.packet import icmp


class ovs_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting OVS Controller')

        self.ctl = kwargs.get('controller', None)

    def pre_exit(self):
     # Terminate the OVS SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        tech = kwargs.get('type', 'high-throughput')
        s_id = kwargs.get('s_id', None)

        source = kwargs.get('source', '100.0.0.1')
        destination = kwargs.get('destination', '100.1.0.10')

        index = destination.split('.')[1]
        if index == 1:
            out_port = 3
        else: #index == 2:
            out_port = 2

        if 'h00' not in self.ctl.switches:
            sleep(10)

        match_0 = self.ctl.switches['h00'].parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_dst=(destination, '255.255.0.0'),
                ipv4_src=(source, '255.255.0.0'))
        actions_0 = [self.ctl.switches['h00'].parser.OFPActionOutput(out_port)]
    
        self.ctl.add_flow(self.ctl.switches['h00'], 0, match_0, actions_0)

        match_1 = self.ctl.switches['h00'].parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=(source, '255.255.0.0'),
                ipv4_dst=(destination, '255.255.0.0'))
        actions_1 = [self.ctl.switches['h00'].parser.OFPActionOutput(1)]
    
        self.ctl.add_flow(self.ctl.switches['h00'], 0, match_1, actions_1)

        match_2 = self.ctl.switches['h01'].parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=(source, '255.255.0.0'),
                ipv4_dst=(destination, '255.255.0.0'))
        actions_2 = [self.ctl.switches['h01'].parser.OFPActionOutput(out_port)]
    
        self.ctl.add_flow(self.ctl.switches['h01'], 0, match_2, actions_2)

        match_3 = self.ctl.switches['h01'].parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_dst=(destination, '255.255.0.0'),
                ipv4_src=(source, '255.255.0.0'))
        actions_3 = [self.ctl.switches['h01'].parser.OFPActionOutput(1)]
    
        self.ctl.add_flow(self.ctl.switches['h01'], 0, match_3, actions_3)

        # Return host and port -- TODO may drop port entirely
        return True, {'host': 'sdijsd'}


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Third step: Remove virtual RF front-end
        # TODO do something here


        # Return host and port -- TODO may drop port entirely
        return True, {'s_id': kwargs['s_id']}

class switch(object):
        
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.datapath = kwargs.get('datapath')
        self.ip_addr = kwargs.get('ip_addr', '')

        self.dpid = self.datapath.id
        self.ofproto = self.datapath.ofproto
        self.parser = self.datapath.ofproto_parser

        self.mac_to_port = dict()

        if self.name == 'h00':
            self.port_to_mac = {
                1: "00:16:3e:a4:b4:5e",
                2: "00:16:3e:cd:52:ed",
                3: "00:16:3e:6f:2e:71"
            }
        elif self.name == 'h01':        
            self.port_to_mac = {
                1: "00:16:3e:59:ab:1d",
                2: "00:16:3e:86:c7:c6"}

        else: 
            self.port_to_mac = {
                1: "00:16:3e:e9:d2:54",
                2: "00:16:3e:c4:c5:6e"}


    def add_flow(self, priority, match, actions, buffer_id=None):
        inst = [self.parser.OFPInstructionActions(
            self.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = self.parser.OFPFlowMod(
              datapath=self.datapath,
              buffer_id=buffer_id,
              priority=priority,
              match=match,
              instructions=inst)

        else:
            mod = self.parser.OFPFlowMod(
                datapath=self.datapath,
                priority=priority,
                match=match,
                instructions=inst)

        self.datapath.send_msg(mod)


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        #  self.mac_to_port = dict()

        self.switches = dict()

        self.dpid_to_name = {
            95536754289: 'h00',
            95535344413: 'h01',
            95542363502: 'h02'
        }

        self.dpid_to_ip= {
            95536754289: '10.0.0.1',
            95535344413: '10.0.1.1',
            95542363502: '10.0.2.1'
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
            controller=self
        )

        # Start the OVS SDR Controller Server
        self.ovs_controller_hub = hub.spawn(self.ovs_controller_thread.run)

        print('\t', 'Started OVS Controller')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath

        # Create new switch
        new_switch = switch(
                datapath=datapath,
                name=self.dpid_to_name[datapath.id],
                ip_addr=self.dpid_to_ip[datapath.id])



        # Add switch to dict 
        self.switches[new_switch.name] = new_switch 

        match = new_switch.parser.OFPMatch()
        actions = [new_switch.parser.OFPActionOutput(
            new_switch.ofproto.OFPP_CONTROLLER,
            new_switch.ofproto.OFPCML_NO_BUFFER)]

        new_switch.add_flow(0, match, actions)

        self._base_start(new_switch)
        
    def _base_start(self, switch):
        parser = switch.parser

        if  switch.name == 'h00':
            # Start outputting all packets to port 1
            match = parser.OFPMatch(in_port=(2, 3))
            actions = [parser.OFPActionOutput(1)]
    
            # Add the flow to the switch
            switch.add_flow(1, match, actions)

            if False:
                match_0 = parser.OFPMatch(in_port=(1))
                actions_0 = [parser.OFPActionOutput(3)]
    
                # Add the flow to the switch
                switch.add_flow(1, match_0, actions_0)

        if switch.name in ['h01', 'h02']:
            # In to out 
            actions_1 = [parser.OFPActionOutput(1)]
            match_1 = parser.OFPMatch(in_port=(2))

            # Add the flow to the switch
            switch.add_flow(1, match_1, actions_1)

            # Out to in
            actions_2 = [parser.OFPActionOutput(2)]
            match_2 = parser.OFPMatch(in_port=(1))

            # Add the flow to the switch
            switch.add_flow(1, match_2, actions_2)

        print('Configured Switch ', switch.name)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg

        dpid = self.dpid_to_name[msg.datapath.id]

        if dpid not in self.switches:
            return

        switch = self.switches[dpid]
        ofproto = switch.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]

        if not pkt_ethernet:
            return

        dst = pkt_ethernet.dst
        src = pkt_ethernet.src

        self.logger.info("packet in %s %s %s %s", switch.name, src, dst, 
                in_port if in_port != ofproto.OFPP_LOCAL else 'local')

        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._handle_arp(switch, in_port, pkt_ethernet, pkt_arp)
            return

        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmp = pkt.get_protocol(icmp.icmp)
        if pkt_icmp:
            self._handle_icmp(switch, in_port, pkt_ethernet, pkt_ipv4, pkt_icmp)
            return

        #  if pkt_ethernet.ethertype == ether_types.ETH_TYPE_LLDP:
            #  ignore lldp packet
            #  return



        #  pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        #  if pkt_ipv4:
            #  print('ip', 'src', pkt_ipv4.src, 'dst', pkt_ipv4.dst)

        # learn a mac address to avoid FLOOD next time.
        switch.mac_to_port[src] = in_port

        if dst in switch.mac_to_port:
            out_port = switch.mac_to_port[dst]
        else:
            out_port = ofproto.OFPP_FLOOD


        self.provision_paths(switch, in_port, src, out_port, dst, msg)

    def _send_packet(self, switch, port, pkt):
        ofproto = switch.ofproto
        parser = switch.parser

        pkt.serialize()
        #  self.logger.info("packet-out %s" % (pkt,))

        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=switch.datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        switch.datapath.send_msg(out)

    def _handle_icmp(self, switch, port, pkt_ethernet, pkt_ipv4, pkt_icmp):
        if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
            return
        interface = switch.port_to_mac[port]

        pkt = packet.Packet()

        pkt.add_protocol(ethernet.ethernet(
            ethertype=pkt_ethernet.ethertype,
            dst=pkt_ethernet.src,
            src=interface))

        if pkt_ipv4.dst == switch.ip_addr:
            pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
                                       src=switch.ip_addr,
                                       proto=pkt_ipv4.proto))

            pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
                                       code=icmp.ICMP_ECHO_REPLY_CODE,
                                       csum=0,
                                       data=pkt_icmp.data))

            self._send_packet(switch, port, pkt)

    def _handle_arp(self, switch, port, pkt_ethernet, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        interface = switch.port_to_mac[port]

        pkt = packet.Packet()

        pkt.add_protocol(ethernet.ethernet(
            ethertype=pkt_ethernet.ethertype,
            dst=pkt_ethernet.src,
            src=interface))

        if pkt_arp.dst_ip == switch.ip_addr:
            pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=interface,
                                     src_ip=switch.ip_addr,
                                     dst_mac=pkt_arp.src_mac,
                                     dst_ip=pkt_arp.src_ip))
            self._send_packet(switch, port, pkt)



    def provision_paths(self, switch, in_port, src, out_port, dst, msg):
        parser = switch.parser
        ofproto = switch.ofproto

        actions = [parser.OFPActionOutput(out_port)]
        #  print(self.mac_to_port)

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                switch.add_flow(1, match, actions, msg.buffer_id)
                return
            else:
                switch.add_flow(1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=switch.datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        switch.datapath.send_msg(out)



