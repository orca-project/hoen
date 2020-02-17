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

def cls():
    system('cls' if name=='nt' else 'clear')

class core_network_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # LXD Controller Handler
        self.lxd_ctl = ctl_base(
            name="LXD",
            host_key="LXD_host",
            port_key="LXD_port",
            default_host="127.0.0.1",
            default_port="3600",
            request_key="lxd_req",
            reply_key="lxd_rep",
            create_msg='lcc_crs',
            request_msg='lcc_rrs',
            update_msg='lcc_urs',
            delete_msg='lcc_drs')


    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Get the slice requirements
        s_req = kwargs.get('requirements', None)
        # Get the slice distribution
        s_dis = kwargs.get('distribution', "ubuntu-19.10-plain")

        # Append it to the list of service IDs
        self.s_ids[s_id] = {"requirements": s_req,
                            "distribution": s_dis}

        # Send message to LXD CN controller
        self._log("Distribution:", s_dis, 'Requirements:', str(s_req))
        self._log('Delegating it to the LXD Controller')

        # Send the message to create a slice
        success, msg = self.lxd_ctl.create_slice(
                **{'s_id': s_id, 's_distro': s_dis })

        # Inform the user about the creation
        return success, msg

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Get the slice requirements
        s_req = self.s_ids[s_id]['requirements']
        # Get the slice distribution
        s_dis = self.s_ids[s_id]['distribution']

        # Send message to LXD SDN controller
        self._log("Distribution:", s_dis, 'Requirements:', str(s_req))
        self._log('Delegating it to the LXD Controller')

        # Send message to remove slice
        success, msg = self.lxd_ctl.delete_slice(
                **{'s_id': s_id, 'ditribution': s_dis})

        # Inform the user about the removal
        return success, msg


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Core Network Orchestrator thread
        core_network_orchestrator_thread = core_network_orchestrator(
            name='CN',
            req_header='cn_req',
            rep_header='cn_rep',
            error_msg='msg_err',
            create_msg='cn_cc',
            request_msg='cn_rc',
            update_msg='cn_uc',
            delete_msg='cn_dc',
            host='127.0.0.1',
            port=2300)

        # Start the Core Network Orchestrator
        core_network_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Core Orchestrator Server
        core_network_orchestrator_thread.safe_shutdown()
