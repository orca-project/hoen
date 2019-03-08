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
from ryu.lib.packet import ether_types


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

    def __init__(self, datapath, name=""):
        self.datapath = datapath
        self.dpid = datapath.id
        self.ofproto = datapath.ofproto
        self.parser = datapath.ofproto_parser
        self.name = name

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = dict()

        self.switches = dict()

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
            controller=self
        )

        # Start the OVS SDR Controller Server
        self.ovs_controller_hub = hub.spawn(self.ovs_controller_thread.run)

        print('\t', 'Started OVS Controller')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath

        # Get the switch's name
        name = self.dpid_to_name[datapath.id]
        new_switch = switch(datapath, name)

        self.switches[name] = new_switch 

        match = new_switch.parser.OFPMatch()
        actions = [new_switch.parser.OFPActionOutput(
            new_switch.ofproto.OFPP_CONTROLLER,
            new_switch.ofproto.OFPCML_NO_BUFFER)]

        self.add_flow(new_switch, 0, match, actions)

        self._base_start(new_switch)
        
    def _base_start(self, switch):
        parser = switch.parser

        if  switch.name== 'h00':
            # Start outputting all packets to port 1
            match = parser.OFPMatch(in_port=(2, 3))
            actions = [parser.OFPActionOutput(1)]
    
            # Add the flow to the switch
            self.add_flow(switch, 1, match, actions)

            if False:
                match_0 = parser.OFPMatch(in_port=(1))
                actions_0 = [parser.OFPActionOutput(3)]
    
                # Add the flow to the switch
                self.add_flow(switch, 1, match_0, actions_0)

        if switch.name in ['h01', 'h02']:
            # In to out 
            actions_1 = [parser.OFPActionOutput(1)]
            match_1 = parser.OFPMatch(in_port=(2))

            # Add the flow to the switch
            self.add_flow(switch, 1, match_1, actions_1)

            # Out to in
            actions_2 = [parser.OFPActionOutput(2)]
            match_2 = parser.OFPMatch(in_port=(1))

            # Add the flow to the switch
            self.add_flow(switch, 1, match_2, actions_2)

        print('Configured Switch ', switch.name)


    def add_flow(self, switch, priority, match, actions, buffer_id=None):
        ofproto = switch.ofproto
        parser = switch.parser

        print(match, actions)
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=switch, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=switch, priority=priority,
                                    match=match, instructions=inst)
        switch.datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        switch = self.switches[self.dpid_to_name[msg.datapath.id]]
        ofproto = switch.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        self.mac_to_port.setdefault(switch.name, {})

        self.logger.info("packet in %s %s %s %s", switch.name, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[switch.name][src] = in_port

        if dst in self.mac_to_port[switch.name]:
            out_port = self.mac_to_port[switch.name][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        self.provision_paths(switch, in_port, src, out_port, dst, msg)

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
                self.add_flow(switch, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(switch, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=switch.datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        switch.datapath.send_msg(out)



