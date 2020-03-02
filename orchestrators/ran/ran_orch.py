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

class radio_access_network_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # OpenWiFi Controller Handler
        self.opw_ctl = ctl_base(
            name="OPW",
            host_key="OPW_host",
            port_key="OPW_port",
            default_host="0.0.0.0",
            default_port="2100",
            request_key="opw_req",
            reply_key="opw_rep",
            create_msg='owc_crs',
            request_msg='owc_rrs',
            update_msg='owc_urs',
            delete_msg='owc_drs')

        # Dictionary mapping UE's MAC addresses
        self.service_to_mac = {
            'be': '14:AB:C5:42:B7:33',
            'urllc': 'B8:27:EB:BE:C1:F1',
            'emmb': '88:29:9C:02:24:EF'
        }
        #TODO We might loads this from a file and allow reloading it

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Get the slice requirements
        s_req = kwargs.get('requirements', None)
        # Get the type of service
        s_ser = kwargs.get('service', 'be')

        # Check whether the type of service is known
        if s_ser not in self.service_to_mac.keys():
            return False, "Invalid type of service:" + str(s_ser)

        # Get MAC address associated with service and map it to 32 bits
        s_mac = self.service_to_mac[s_ser].replace(":","")[4:]

        # TODO Calculate the amount of resources

        # TODO decide which slice to use
        i_sln = 0

        # TODO Implement function to create new slice

        # Send message to OpenWiFi RAN controller
        self._log("Service:", s_ser, 'Requirements:', s_req, "Slice #", i_sln)
        self._log('Delegating it to the OPW Controller')

        # Send the message to create a slice
        success, msg = self.opw_ctl.create_slice(
            **{'s_id': s_id, 's_mac': s_mac, "i_sln": i_sln})

        # Append it to the list of service IDs
        self.s_ids[s_id] = {"requirements": s_req,
                            "service": s_ser,
                            "slice": i_sln,
                            "MAC": (self.service_to_mac[s_ser], s_mac),
                            "destination": msg['destination']}

        # Inform the user about the creation
        return success, msg

    def request_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Create container to hold slice information
        info = {}
        # Iterate over all virtual radios
        for virtual_radio in s_ids.keys():
            # If going for a specific S_ID but it does not match
            if (s_id) and (s_id != virtual_radio):
                continue

            # Log event and return
            self._log("Found virtual radio:", vr)
            # Send message to OpenWifi RAN controller
            self._log('Delegating it to the OpenWiFi Controller')

            # TODO append information from the slice duration and length
            info[s_id] = {
                    "service": s_ids[s_id]["service"],
                    "MAC": s_ids[s_id]["MAC"][0],
                    "slice": { "index": s_ids[s_id]["slice"]}
            }

            # Send the message to create a slice
            success, msg = self.opw_ctl.request_slice(**{'s_id': s_id})

            # If the Controller answered correctly
            if success:
                 # Update info with controller-specific data
                info[s_id]['slice'].update({
                    "start": msg.get[s_id]["start"],
                    "end": msg.get[s_id]["end"],
                    "length": msg.get[s_id]["length"]})

            # Otherwise, include the error
            else:
                # Return error message
                info[s_id]['slice'].update({"info": msg})


        # If there's an S_ID but the result was empty
        return (False, "Virtual radio missing.") \
            if (s_id and not info) else (True, info)


    def update_slice(self, **kwargs):
        pass

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Send message to OpenWiFi RAN controller
        self._log("Service:", s_ser, 'Requirements:', s_req, "Slice #", i_sln)
        # Send message to OpenWifi SDR controller
        self._log('Delegating it to the OpenWiFi Controller')

        # Send message to remove slice
        success, msg = self.opw_ctl.delete_slice(**{'s_id': s_id})

        # Inform the user about the removal
        return success, msg


if __name__ == "__main__":
    # clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the Radio Access Network Orchestrator thread
        radio_access_network_orchestrator_thread = \
                radio_access_network_orchestrator(
            name='RAN',
            req_header='rn_req',
            rep_header='rn_rep',
            error_msg='msg_err',
            create_msg='rn_cc',
            request_msg='rn_rc',
            update_msg='rn_uc',
            delete_msg='rn_dc',
            host='0.0.0.0',
            port=2300)

        # Start the Radio Access Network Orchestrator
        radio_access_network_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Radio Access Network Orchestrator Server
        radio_access_network_orchestrator_thread.safe_shutdown()
