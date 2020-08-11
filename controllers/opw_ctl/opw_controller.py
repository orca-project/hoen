#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller, cls
# Import signal
import signal
# Import the Sleep function from the Time module
from time import sleep
# Import the bash method from the bash module
from bash import bash
# Import the ArgParse module
import argparse

# Import the Omapi object from the pypureomapi
from pypureomapi import Omapi, OmapiErrorNotFound, OmapiError


def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='OpenWifi SDR Controller')

    parser.add_argument(
        '-m', '--skip_modules',
        required=False,
        action='store_true',
        help='Skip loading kernel modules')
    parser.add_argument(
        '-n', '--skip_network',
        required=False,
        action='store_true',
        help='Skip configuring networking')
    parser.add_argument(
        '-a', '--skip_ap',
        required=False,
        action='store_true',
        help='Skip starting Hostapd')

    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    return arg_dict


class opw_controller(base_controller):

    def post_init(self, **kwargs):
        # Get parameters from keyword arguments
        skip_modules = kwargs.get("skip_modules", False)
        skip_network = kwargs.get("skip_network", False)
        skip_ap = kwargs.get("skip_ap", False)
        # Extra options
        self.sdr_dev = kwargs.get("sdr_dev", "sdr0")
        #  self.lan_ip = kwargs.get("lan_ip", "192.168.13.1")
        self.lan_ip = kwargs.get("lan_ip", "10.0.0.1")
        #  gw_ip = kwargs.get("gw_ip", "134.226.55.211")
        gw_dev = kwargs.get("gw_dev", "eth0")
        ap_config_path = kwargs.get("ap_path",
                                    "/root/openwifi/hostapd-openwifi.conf")
        openwifi_path = kwargs.get("openwifi_path", "/root/openwifi")

        # Stop Network Manager
        bash("service network-manager stop")
        self._log("Stopped Network Manager")

        # If loading kernel modules
        if not skip_modules:
            fpga_dev_path = "/sys/bus/iio/devices/iio:device2"
            filter_file = "openwifi_ad9361_fir.ftr"

            # Load mac80211 kernel module
            bash("modprobe mac80211")
            self._log("Loaded 'mac80211' kernel module")

            # If the SDR kernel module is loaded
            if bool(bash("lsmod | grep sdr")):
                # Remove SDR kernel module
                bash("rmmod sdr")
                self._log("Removed 'sdr' kernel module")

            # List of custom kernel modules
            module_list = {"first_batch": ["xilinx_dma", "tx_intf",
                                           "ad9361_drv"],
                           "second_batch": ["rx_intf", "openofdm_tx",
                                            "openofdm_rx", "xpu", "sdr"]}

            # Device configuration dictionary
            device_config = {
                "first_batch": {
                    "in_voltage_rf_bandwidth": "17500000",
                    "out_voltage_rf_bandwidth": "37500000",
                    "in_voltage_sampling_frequency": "40000000",
                    "out_voltage_sampling_frequency": "40000000",
                    "out_altvoltage0_RX_LO_frequency": "5240000000",
                    "out_altvoltage1_TX_LO_frequency": "5250000000"
                },
                "second_batch": {
                    "in_voltage_filter_fir_en": "1",
                    "out_voltage_filter_fir_en": "0",
                    "in_voltage0_gain_control_mode": "fast_attack",
                    "in_voltage1_gain_control_mode": "fast_attack",
                    "in_voltage0_hardwaregain": "70",
                    "in_voltage1_hardwaregain": "70",
                    "out_voltage0_hardwaregain": "89",
                    "out_voltage1_hardwaregain": "0"
                }
            }

            # Iterate over the first batch
            for submodule in module_list['first_batch']:
                # Check whether the module is loaded
                if bool(bash("lsmod | grep {0}".format(submodule))):
                    # Removing current version of the module
                    bash("rmmod {0}".format(submodule))
                # Installing new version of the module
                bash("insmod {0}/{1}.ko".format(openwifi_path, submodule))
                # Check installation of kernel module
                sleep(1)
                if not bash("lsmod | grep {0}".format(submodule)).code:
                    self._log("Loaded", submodule, "kernel module")

                else:
                    self._log("Not loaded", submodule, "kernel module")

            # Iterate over the first batch of parameters
            for parameter in device_config["first_batch"].keys():
                # Update the parameter value
                bash("echo {0} > {1}/{2}".format(
                         device_config["first_batch"][parameter],
                         fpga_dev_path,
                         parameter))
                bash("sync")
                sleep(0.5)

            # Filter file string
            filter_str = "cat {0}/{1} > {2}/filter_fir_config"
            # Load filter response values
            bash(filter_str.format(openwifi_path, filter_file, fpga_dev_path))

            # Iterate over the second batch of parameters
            for parameter in device_config["second_batch"].keys():
                # Update the parameter value
                bash("echo {0} > {1}/{2}".format(
                    device_config["second_batch"][parameter],
                    fpga_dev_path,
                    parameter))
                bash("sync")
                sleep(0.5)

            # Iterate over the second batch
            for submodule in module_list['second_batch']:
                # Check whether the module is loaded
                if bool(bash("lsmod | grep {0}".format(submodule))):
                    # Removing current version of the module
                    bash("rmmod {0}".format(submodule))

                # Installing new version of the module
                bash("insmod {0}/{1}.ko".format(openwifi_path, submodule))
                sleep(1)
                # Check installation of kernel module
                if not bash("lsmod | grep {0}".format(submodule)).code:
                    self._log("Loaded", submodule, "kernel module")

            # Sleep for 10 seconds and log event
            self._log("Waiting for configurations to take effect")
            sleep(10)
            self._log("Configured kernel modules and FPGA")

        # If configuring routing and networking
        if not skip_network:
            # Configure the SDR interface's IP
            bash("ifconfig {0} {1} netmask 255.255.255.0".format(self.sdr_dev,
                                                                 self.lan_ip))
            self._log("Set {0} interface IP's to: {1}".format(self.sdr_dev,
                                                              self.lan_ip))

            # Set the default route through eth0
            #  bash("ip route add default via {0} dev eth0".format(gw_ip))
            bash("ip route add default dev {0}".format(gw_dev))
            #  self._log("Set default gateway to: {0}".format(gw_ip))
            self._log("Set default gateway to: {0}".format(gw_dev))

            # Sleep for 2 seconds and log event
            self._log("Configured routing and networking")


        # Stop DHCP server
        bash("service isc-dhcp-server stop")
        # Clear current leases
        bash("echo '' > /var/lib/dhcp/dhcpd.leases")
        # Start DHCP server
        bash("service isc-dhcp-server start")

        sleep(5)

        self._log("Restarted DHCP server")

        # Create a list of possible client IPs
        self.dhcp_pool = set(".".join(self.lan_ip.split(".")[:-1]) + "." +
                                str(x) for x in range(110,200))

        # OMAPI Configuration parameters
        omapi_host = "127.0.0.1"
        omapi_port = 7911
        omapi_keyname = b"defomapi"
        omapi_key = b"SmR3+XVX95vDQ3SaZD1B7xTXYTcwNg/AZn9DAsJS" + \
            b"9oESudsTQ5bRMaSt bHPyOJchWlXF2Q6CuhSD70eTNl5hOg=="

        # Create OMAPI object
        self.omapi = Omapi(omapi_host, omapi_port, omapi_keyname, omapi_key)


        # If starting the access point
        if not skip_ap:
            # If there is a Host AP Daemon running in the background
            if bool(bash("ps -aux | grep [h]ostapd")):
                # Kill the process
                bash("killall hostapd")
                self._log("Stopped existing hostapd instances")

            # Run this 10 times or until hostapd starts
            for x in range(10):
                # Start Host AP Daemon in the background and log event
                apd = bash("hostapd -B {0}".format(ap_config_path)).code

                # If it worked
                if not apd:
                    break

                self._log("Trying to start the AP, #", x+1)
                sleep(1)

            # If we could not configure the AP
            if apd:
                raise Exception("Could not configure AP")

            # Log event
            self._log("Configured access point")


        # TODO This ought to change in the future
        # List of currently support RAN slices
        self.ran_slice_list = [{"index": 0, "available": True},
                               {"index": 1, "available": True},
                               {"index": 2, "available": True},
                               {"index": 3, "available": True},
                            ]

        # Iterate over existing slices
        for ran_slice in self.ran_slice_list:
            # Set current slice index
            idx = bash("sdrctl dev {0} set slice_idx {1}".format(
                    self.sdr_dev,
                    ran_slice['index'])).code

            # Clear MAC addresses associated with slice
            cls = bash("sdrctl dev {0} set addr {1}".format(
                    self.sdr_dev,
                    "00000000")).code

            # Log event
            self._log("Failed clearing slice #" if cls else "Cleared slice #",
                      ran_slice["index"])

        # Sync all slices
        sync = bash("sdrctl dev {0} set slice_idx 4".format(self.sdr_dev)).code

        # Output status message and/or exit
        if not sync:
            self._log("Synchronised all RAN slices!")
        else:
            self._log("Failed synchronising RAN slices.")
            exit(10)


    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))
        s_mac = str(kwargs.get('s_mac', None))
        i_sln = int(kwargs.get("slice", {}).get('number', 0))

        # If the MAC address is invalid
        if not s_mac or s_mac is None:
            return False, "Malformatted MAC address:" + str(s_mac)

        # Iterate over the current slices
        for sid in self.s_ids:
            # Check whether the entered MAC address is already being used
            if self.s_ids[sid] and (s_mac == self.s_ids[sid]['mac']):
                # Return error
                return False, "MAC address already associated to slice: " + sid

        # Check whether the slice number is valid
        if i_sln not in [x['index'] for x in self.ran_slice_list]:
            # If not, return error
            return False, "Invalid slice number:" + str(i_sln)

        # Check whether there an available slice
        elif not self.ran_slice_list[i_sln]['available']:
            # If not, return error
            return False, "Slice #" + str(i_sln) + " is not available."


        # Check whether the given MAC address has a current DHCP lease
        try:
            # Try to check it
            self.omapi.lookup_by_host(mac=s_mac)

        # If it doesn't work, great
        except OmapiErrorNotFound:
            pass

        # Otherwise, clear it
        else:
            self.omapi.del_host(s_mac)

        # Get the first available IP address
        lease_ip = self.dhcp_pool.pop()

        # Add host to the DHCP subnet
        try:
            self.omapi.add_host(lease_ip, s_mac)

        # If if failed
        except OmapiError:
            # Report to the hyperstrator
            return False, "DHCP lease creation failed."

        # Log event
        self._log("Set", s_mac, "IP to:", lease_ip)

        # Get the slice configuration parameters
        i_start = int(kwargs.get("slice", {}).get('start', 0))
        i_end   = int(kwargs.get("slice", {}).get('end',   49999))
        i_total = int(kwargs.get("slice", {}).get('total', 50000))

        # Set the slice in question
        bash("sdrctl dev {0} set slice_idx {1}".format(self.sdr_dev, i_sln))

        # Set the slice configuration
        bash("sdrctl dev {0} set slice_start {1}".format(self.sdr_dev, i_start))
        bash("sdrctl dev {0} set slice_end {1}".format(self.sdr_dev, i_end))
        bash("sdrctl dev {0} set slice_total {1}".format(self.sdr_dev, i_total))

        # Log event
        self._log("Set slice", i_sln, " start/end/total to",
                  i_start, "/", i_end, "/", i_total)

        # Get MAC address associated with service and map it to 32 bits
        s_mac_32 = s_mac.replace(":","")[4:]

        # Add MAC address to SDRCTL
        sla = bash("sdrctl dev {0} set addr {1}".format(
            self.sdr_dev,
            s_mac_32)).code

        # Sync all commands
        sync = bash("sdrctl dev {0} set slice_idx 4".format(self.sdr_dev)).code

        if sla or sync:
            return False, "Slice creation railed."

        # Iterate over the slice slice
        for i, x in enumerate(self.ran_slice_list):
            # If matching the slice number
            if x["index"] == i_sln:
                # Toggle flag
                self.ran_slice_list[i]['available'] = False

        # Create a slice entry
        self.s_ids[s_id] = {
            "mac": s_mac,
            "ip": lease_ip,
            "slice": {
                "number": i_sln,
                "start": i_start,
                "end": i_end,
                "total": i_total}
        }

        # Log event
        self._log("Created slice", s_id)

        return True, {"s_id": s_id, "destination": lease_ip}


    def request_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Container to told the requested information
        msg = {}
        # Iterate over all slices
        for virtual_radio in self.s_ids:
            # If requesting info about a specific S_ID but it is not a match
            if s_id and s_id != virtual_radio:
                continue

            # Log event
            self._log("Found virtual radio:", virtual_radio)

            # Append this information to the output dictionary
            msg[s_id] = {
                "mac": self.s_ids[virtual_radio]["mac"],
                "ip": self.s_ids[virtual_radio]["ip"],
                "slice": self.s_ids[virtual_radio]["slice"]
            }

        # Return flag and dictionary in case positive
        return (False, "Virtual radio missing") if \
            (s_id and not msg) else (True, msg)


    def update_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Return state
        return True, "This is a stub"


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Get the client's MAC address
        s_mac= self.s_ids[s_id]["mac"]
        # Get the slice number
        i_sln = self.s_ids[s_id]["slice"]["number"]

        # Remove host from the DHCP subnet
        self.omapi.del_host(s_mac)

        # Set the slice in question
        bash("sdrctl dev {0} set slice_idx {1}".format(self.sdr_dev, i_sln))

        # Try to clear the slice
        cls = bash("sdrctl dev {0} set addr {1}".format(
            self.sdr_dev,
            "00000000")).code

        # If the last command failed
        if cls:
            return False, "Could not remove MAC from slice #" + str(i_lsn)

        # Set the default slice configuration
        s = bash("sdrctl dev {0} set slice_start {1}".format(
            self.sdr_dev,
            0)).code
        e = bash("sdrctl dev {0} set slice_end {1}".format(
            self.sdr_dev,
            49999)).code
        t = bash("sdrctl dev {0} set slice_total {1}".format(
            self.sdr_dev,
            50000)).code

        # Sync all commands
        sync = bash("sdrctl dev {0} set slice_idx 4".format(self.sdr_dev)).code

        # If any of the precious commands failed
        if any([s,e,t, sync]):
            return False, "Failed reverting slice to default parameters."

        # Iterate over the slice slice
        for i, x in enumerate(self.ran_slice_list):
            # If matching the slice number
            if x["index"] == i_sln:
                # Toggle flag
                self.ran_slice_list[i]['available'] = True

        # Return state
        return True, {"s_id": s_id}


if __name__ == "__main__":
    # Clear screen
    cls()

    # Parse CLI arguments
    kwargs = parse_cli_args()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the OpenWiFi Controller
        opw_controller_thread = opw_controller(
            name='OpenWiFi',
            req_header='opw_req',  # Don't modify
            rep_header='opw_rep',  # Don't modify
            info_msg='ns_owc',
            create_msg='owc_crs',
            request_msg='owc_rrs',
            update_msg='owc_urs',
            delete_msg='owc_drs',
            host='0.0.0.0',
            port=3100,
	    **kwargs
	)

        # Start the OpenWiFi Controller Server
        opw_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the OpenWiFi Controller Server
        opw_controller_thread.safe_shutdown()
