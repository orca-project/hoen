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
            default_port="3300",
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
                            "slice": {"index": i_sln},
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
        for virtual_radio in self.s_ids.keys():
            # If going for a specific S_ID but it does not match
            if (s_id) and (s_id != virtual_radio):
                continue

            # Log event and return
            self._log("Found virtual radio:", virtual_radio)
            # Send message to OpenWifi RAN controller
            self._log('Delegating it to the OpenWiFi Controller')

            # TODO append information from the slice duration and length
            info[virtual_radio] = {
                    "service": self.s_ids[virtual_radio]["service"],
                    "MAC": self.s_ids[virtual_radio]["MAC"][0],
                    "slice": self.s_ids[virtual_radio]["slice"]
            }

            # Send the message to create a slice
            success, msg = self.opw_ctl.request_slice(**{'s_id': virtual_radio})

            # If the Controller answered correctly
            if success and (virtual_radio in msg):
                 # Update info with controller-specific data
                info[virtual_radio]['slice'].update({
                    "start": msg[virtual_radio].get("start", "Not reported"),
                    "end": msg[virtual_radio].get("end", "Not reported"),
                    "length": msg[virtual_radio].get("length", "Not reported")
                })

            # Otherwise, include the error
            else:
                # Return error message
                info[virtual_radio]['slice'].update({"info": msg})

        # If there's an S_ID but the result was empty
        return (False, "Virtual radio missing.") \
            if (s_id and not info) else (True, info)


    def update_slice(self, **kwargs):
        pass

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Get service infroamtion
        s_req = self.s_ids[s_id]["requirements"]
        s_ser = self.s_ids[s_id]["service"]
        i_sln = self.s_ids[s_id]["slice"]["index"]

        # Send message to OpenWiFi RAN controller
        self._log("Service:", s_ser, 'Requirements:', s_req, "Slice #", i_sln)
        # Send message to OpenWifi SDR controller
        self._log('Delegating it to the OpenWiFi Controller')

        # Send message to remove slice
        success, msg = self.opw_ctl.delete_slice(**{'s_id': s_id})

        # TODO check whether to remove unused slices

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
            port=2100)

        # Start the Radio Access Network Orchestrator
        radio_access_network_orchestrator_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Radio Access Network Orchestrator Server
        radio_access_network_orchestrator_thread.safe_shutdown()
