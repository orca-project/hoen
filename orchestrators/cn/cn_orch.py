#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Orchestrator
from base_orchestrator.base_orchestrator import base_orchestrator, ctl_base, cls
# Import signal
import signal

class core_network_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # LXD Controller Handler
        self.lxd_ctl = ctl_base(
            name="LXD",
            host_key="LXD_host",
            port_key="LXD_port",
            default_host="127.0.0.1",
            default_port="3300",
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
        # Get the service
        s_ser = kwargs.get('service', "best-effort")

        # Append it to the list of service IDs
        self.s_ids[s_id] = {"requirements": s_req,
                            "service": s_ser}

        # Send message to LXD CN controller
        self._log("Service:", s_ser, 'Requirements:', str(s_req))
        self._log('Delegating it to the LXD Controller')

        # TODO make a smarter allocation
        f_ram = 2.0 if s_ser in ["embb", "high-throughput"] else 1.0
        i_cpu = 2 if s_ser in ["urllc", "low-latency"] else 1

        # Send the message to create a slice
        success, msg = self.lxd_ctl.create_slice(
            **{'s_id': s_id, 'service': s_ser, "f_ram": f_ram, "i_cpu": i_cpu})

        # Inform the user about the creation
        return success, msg


    def request_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Send message to LXD CN controller
        self._log('Delegating it to the LXD Controller')

        # Send the message to create a slice
        success, msg = self.lxd_ctl.request_slice(**{'s_id': s_id})

        # Inform the user about the creation
        return success, msg


    def update_slice(self, **kwargs):
        pass


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Get the slice requirements
        s_req = self.s_ids[s_id]['requirements']
        # Get the slice service
        s_ser = self.s_ids[s_id]['service']

        # Send message to LXD SDN controller
        self._log("Service:", s_ser, 'Requirements:', str(s_req))
        self._log('Delegating it to the LXD Controller')

        # Send message to remove slice
        success, msg = self.lxd_ctl.delete_slice(**{'s_id': s_id})

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
            host='0.0.0.0',
            port=2300)

        # Start the Core Network Orchestrator
        core_network_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Core Orchestrator Server
        core_network_orchestrator_thread.safe_shutdown()
