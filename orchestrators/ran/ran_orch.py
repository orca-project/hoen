#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Orchestrator
from base_orchestrator.base_orchestrator import base_orchestrator, ctl_base, cls
# Import the System and Name methods from the OS module
from os import system, name

import datetime

# Import signal
import signal


class radio_access_network_orchestrator(base_orchestrator):

    def post_init(self, **kwargs):
        # OpenWiFi Controller Handler
        self.opw_ctl = ctl_base(
            name="OPW",
            host_key="OPW_host",
            port_key="OPW_port",
            default_host="127.0.0.1",
            default_port="3100",
            request_key="opw_req",
            reply_key="opw_rep",
            info_msg='ns_owc',
            create_msg='owc_crs',
            request_msg='owc_rrs',
            update_msg='owc_urs',
            delete_msg='owc_drs')

        # Dictionary mapping service types to slice numbers
        self.service_to_queue = {
            'best-effort': 3,
            'embb': 1,
            'urllc': 0
        }

        # Keep track of the allocated and free radio resources
        self.radio_resources = [{'queue': None,
                                 'start': 0,
                                 'end': 49999}]

        # Dictionary mapping UE's MAC addresses
        self.service_to_mac = {
            #  'best-effort': '14:AB:C5:42:B7:33', # New Dell
            'best-effort': '14:AB:C5:42:B7:33', # New Dell
            #  'embb': '14:AB:C5:42:B7:33', # New Dell
            'urllc': 'B8:27:EB:BE:C1:F1', # RasPi
            'embb': '88:29:9C:02:24:EF' # Phone
            #  'embb': 'F8:16:54:4C:E1:A4' # Old Dell
        }
        #TODO We might loads this from a file and allow reloading it

    def network_info(self, **kwargs):
        # Extract parameters from keyword arguments
        s_ns = kwargs.get('s_ns', None)

        # Send message to OpenWiFi RAN controller
        self._log("Retrieve information about the", self.name),

        # Inform the user about the network segment
        return True, {'ran': {"resource_allocation": self.radio_resources}}


    def create_slice(self, **kwargs):
        a = datetime.datetime.now()
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)
        # Get the slice requirements
        s_req = kwargs.get('requirements', None)
        # Get the type of service
        s_ser = kwargs.get('service', 'best-effort')

        # Check whether the type of service is known
        if s_ser not in self.service_to_mac.keys():
                return False, "Invalid type of service: " + str(s_ser)

        # Get MAC address associated with service
        s_mac = self.service_to_mac[s_ser]

        # Apply defaults and sanitise input
        i_thx = s_req.get("throughput", 1)
        i_thx = float(i_thx) if i_thx is not None else 1

        i_del = s_req.get("latency", 100)
        i_del = float(i_del) if i_del is not None else 200

        # Calculate the required amount of resources
        eq_thx = max((i_thx - 0.5786)  / 14.19, 0.01)
        eq_del = max((148.6 - i_del) / 133.2, 0.01)

        # Get the minimum amount to suffice both delay and throughput
        req_resources = int(50000 * max(eq_thx, eq_del)) - 1

        # TODO Dirty fix to handle approximation error
        if req_resources >= 50000 and req_resources <= 51000:
            req_resources = 49999

        # If requiring too many resources
        if req_resources >= 50000:
            return False, "Unfeasible request."

        # TODO Dirty way around
        if s_ser == 'best-effort':
            req_resources = 4999

        # Try to allocate radio sources
        allocated = False
        # Allocate over the list of radio resources
        for index, resource in enumerate(self.radio_resources):
            # If there's a free chunk of airtime
            if resource['queue'] is None and \
                    resource['end'] - resource['start'] >= req_resources:
                # Slice it over
                self.radio_resources.insert(
                    index+1,
                    {
                        'queue': None,
                        'start': resource['start'] + req_resources,
                        'end': resource['end']
                })

                self.radio_resources[index] = {
                        'queue': self.service_to_queue.get(s_ser, 3),
                        'start': resource['start'],
                        'end': resource['start'] + req_resources - 1
                }
                allocated  = True
                break

        # If we could not allocate the current request
        if not allocated:
            return False, 'Not enough radio resources.'


        # Express the amount of resources in a way that SDRCTL can understand
        i_start = self.radio_resources[index]['start']
        i_end = self.radio_resources[index]['end']
        i_total = 50000
        i_sln = self.radio_resources[index]['queue']

        # Send message to OpenWiFi RAN controller
        self._log("Service:", s_ser, 'Requirements:', s_req, "Slice #", i_sln)
        self._log('Delegating it to the OPW Controller')

        b = datetime.datetime.now()

        c = b -a
        print(c.microseconds)
        # Send the message to create a slice
        success, msg = self.opw_ctl.create_slice(
            **{'s_id': s_id, 's_mac': s_mac,
               "slice": {
                   "number": i_sln,
                   'start': i_start,
                   'end': i_end,
                   'total': i_total}
               })

        d = datetime.datetime.now()

        if success:
            # Append it to the list of service IDs
            self.s_ids[s_id] = {"requirements": s_req,
                                "service": s_ser,
                                "slice": {"number": i_sln},
                                "MAC": s_mac,
                                "destination": msg['destination']}


        e = datetime.datetime.now()

        f = e - d
        print(f.microseconds)
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

            # Create entry with orchestrator-only info about the virtual radio
            info[virtual_radio] = {
                    "service": self.s_ids[virtual_radio]["service"],
            }

            # Send the message to create a slice
            success, msg = self.opw_ctl.request_slice(**{'s_id': virtual_radio})

            # If the Controller answered correctly
            if success and (virtual_radio in msg):
                 # Update info with controller-specific data
                info[virtual_radio].update(msg[virtual_radio])

            # Otherwise, include the error
            else:
                # Return error message
                info[virtual_radio]['info'] = msg

        # If there's an S_ID but the result was empty
        return (False, "Virtual radio missing.") \
            if (s_id and not info) else (True, info)


    def update_slice(self, **kwargs):
        pass

    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Get service information
        s_req = self.s_ids[s_id]["requirements"]
        # Get the slice service
        s_ser = self.s_ids[s_id]["service"]
        # Get the slice number
        i_sln = self.s_ids[s_id]["slice"]["number"]

        # Send message to OpenWiFi RAN controller
        self._log("Service:", s_ser, 'Requirements:', s_req, "Slice #", i_sln)
        # Send message to OpenWifi SDR controller
        self._log('Delegating it to the OpenWiFi Controller')

        # Send message to remove slice
        success, msg = self.opw_ctl.delete_slice(**{'s_id': s_id})

        # Clear the allocated resources
        for index, resource in enumerate(self.radio_resources):
            if resource['queue'] == i_sln:
                # Remove queue number
                self.radio_resources[index]['queue'] = None

                # If the next radio is also free
                if (index < len(self.radio_resources)-1) and \
                        self.radio_resources[index+1]['queue'] is None:
                    # Merge two free chunks
                    self.radio_resources[index]['end'] = \
                        self.radio_resources[index+1]['end']
                    # And remove the next one
                    self.radio_resources.pop(index+1)

                # If the previous radio is also free
                if (index > 0) and \
                        self.radio_resources[index-1]['queue'] is None:
                    # Merge two free chunks
                    self.radio_resources[index]['start'] = \
                        self.radio_resources[index-1]['start']
                    # And remove the previous ones
                    self.radio_resources.pop(index-1)

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
            info_msg='ns_rn',
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
