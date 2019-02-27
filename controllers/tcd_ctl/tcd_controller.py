#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from template_controller.template_controller import controller_base
# Import OS
import os
# Import signal
import signal

from grc_manager import grc_manager
from route_manager import route_manager

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


class tcd_controller(controller_base):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting TCD Controller')
        # Start the GRC manager
        self.grc_manager = grc_manager()
        # Start the route manager
        self.route_manager = route_manager()

        # Attach to the USRP
        self.usrp = self.grc_manager.create_sdr()


    def pre_exit(self):
     # Terminate the TCD SDR Controller Server
        self.shutdown_flag.set()
        # Release RATs
        self.grc_manager.remove_rat()
        # Release SDRs
        self.grc_manager.remove_sdr()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        tech = kwargs.get('type', 'high-throughput')
        dirx = kwargs.get('dirx', 'trx')
        s_id = kwargs.get('s_id', None)

        # Check for missing S_ID
        if s_id is None:
            # Return NACK
            return {self.create_nack: {'msg': 'Missing Service ID.'}}

        # Check for invalid direction
        if dirx not in ['rx', 'tx', 'trx']:
            # Return NACK
            return {self.create_nack: {'msg': 'Invalid RAT direction: ' + str(dirx)}}

        # Convert traffic type to RAT
        if tech == 'high-throughput':
            tech = 'lte'
        elif tech == 'low-latency':
            tech = ' iot'
        else:
            # Return NACK
            return {self.create_nack: {'msg': 'Invalid RAT: ' + str(tech)}}


        # First step: Create virtual RF front-end
        # TODO do something here


        # Second step: Create the RAT
        try:
            # Create a new software radio
            rat_id = self.grc_manager.create_rat(technology=tech,
                                                 direction=dirx,
                                                 service_id=s_id)

        # If failed creating software radio
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return {self.create_nack: {"msg": str(e)}}



        # Third step: Configure routes
        try:
            host = self.route_manager.create_route(rat_id=rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return {self.create_nack: {"msg": str(e)}}

        # Return host and port -- TODO may drop port entirely
        return {self.create_ack: {'host': host, "port": 7001}}


    def remove_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Check for missing S_ID
        if s_id is None:
            # Return NACK
            return {self.delete_nack: {'msg': 'Missing Service ID.'}}

        #First Step: Remove the RAT
        try:
            # Remove a software radio
            rat_id = self.grc_manager.remove_rat(s_id=s_id)

        # If it failed removing the software radio
        except Exception as e:
             # Send NACK
            print('\t' + str(e))
            return {self.delete_nack: {"msg": str(e)}}

        # Second step: Remove routes
        try:
            self.route_manager.remove_route(rat_id=rat_id)

        # If failed establishing routes
        except Exception as e:
            # Send NACK
            print('\t' + str(e))
            return {self.delete_nack: {"msg": str(e)}}

        # Third step: Remove virtual RF front-end
        # TODO do something here


        # Return host and port -- TODO may drop port entirely
        return {self.delete_ack: {'s_id': kwargs['s_id']}}


if __name__ == "__main__":
    # Clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the TCD SDR Controller
        tcd_controller_thread = tcd_controller(
            name='TCD',
            req_header='tcd_req', # Don't modify
            rep_header='tcd_rep', # Don't modify
            host='127.0.0.1',
            port=4000)

        # Start the TCD SDR Controller Server
        tcd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the TCD SDR Controller Server
        tcd_controller_thread.pre_exit()

        print('Exiting')
