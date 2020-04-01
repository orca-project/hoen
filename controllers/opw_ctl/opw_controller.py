#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import OS
import os
# Import signal
import signal
# Import the Sleep function from the Time module
from time import sleep
# Import the bash method from the bash module
from bash import bash

# Import datetime and timedelta from the Datetime module
from datetime import datetime, timedelta


class opw_controller(base_controller):

    def post_init(self, **kwargs):
        # Get parameters from keyword arguments
        do_modules = kwargs.get("do_modules", True)
        do_network = kwargs.get("do_network", True)
        do_ap = kwargs.get("do_ap", True)
        # Extra options
        sdr_dev = kwargs.get("sdr_dev", "sdr0")
        lan_ip = kwargs.get("lan_ip", "192.168.13.1")
        gw_ip = kwargs.get("gw_ip", "134.226.55.211")
        ap_config_path = kwargs.get("ap_path",
                                    "/root/openwifi/hostapd-openwifi.conf")
        openwifi_path = kwargs.get("openwifi_path", "/root/openwifi")

        # Stop Network Manager
        bash("service network-manager stop")
        self._log("Stopped Network Manager")

        # If loading kernel modules
        if do_modules:
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
        if do_network:
            # Configure the SDR interface's IP
            bash("ifconfig {0} {1} netmask 255.255.255.0".format(sdr_dev,
                                                                 lan_ip))
            self._log("Set {0} interface IP's to: {1}".format(sdr_dev, lan_ip))

            # Set the default route through eth0
            bash("ip route add default via {0} dev eth0".format(gw_ip))
            self._log("Set default gateway to: {0}".format(gw_ip))

            # Restart DHCP server
            bash("service isc-dhcp-server restart")
            self._log("Restarted DHCP server")

            # Sleep for 5 seconds and log event
            sleep(5)
            self._log("Configured routing and networking")

        # If starting the access point
        if do_ap:
            # If there is a Host AP Daemon running in the background
            if bool(bash("ps -aux | grep [h]ostapd")):
                # Kill the process
                bash("killall hostapd")
                self._log("Stopped existing hostapd instances")

            # Start Host AP Daemon in the background and log event
            apd = bash("hostapd -B {0}".format(ap_config_path)).code

            # Log event
            self._log("Configured access point" if not apd else \
                      "Access point not initialised.")


    def create_slice(self, **kwargs):
       # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))
        #  s_ser = kwargs.get('service', "best-effort")
        s_mac = kwargs.get('mac_addres', None)
        s_air = keargs.get

        # If the MAC address is invalid
        if not s_mac or s_mac is None:
            return False, "Malformatted MAC address:" + str(s_mac)

        # Check whether the entered MAC address is already being used
        #existing_mac = False
        # Iterate over the current slices
        for s_id in self.s_ids:
            # If matching the MAC address
            if s_mac == s_id['mac']:
                # Toggle flag and break
                #existing_mac = True
                #break
                return False, "MAC address already associated to slice: " + s_id

        # Get MAC address associated with service and map it to 32 bits
        s_mac_32 = s_mac.replace(":","")[4:]

        # Add MAC address to SDRCTL
        bash("sdrctl dev sdr0 set addr{0} {1}".format(slice_no, mac_red))



        # check if we have enough resources
        lease_template = 'lease {0} {\n  starts 2 {1};' + \
        '\n  ends 2 {2};\n  tstp 2 {2};\n  cltt 2 {2};' + \
        '\n  binding state active;\n  next binding state free;' + \
        '\n  rewind binding state free;\n  hardware ethernet {3};' + \
        '\n  client-hostname "client";\n}\n'

        # Get the time now, calculate the lease end and format to strings
        time_now = datetime.now()
        lease_start = time_now.strftime('%Y/%m/%d %X')
        lease_end = (time_now+timedelta(minutes=10)).strftime('%Y/%m/%d %X')

        # Fill the lease template with the ne
        lease = lease_template.format(lease_ip, lease_start, lease_end, s_mac)

        # Include the new lease
        bash("cat {0} >> /var/lib/dhcp/dhcpd.leases".format(lease))

        # Restart DHCP server to make changes effective
        bash("service isc-dhcp-server restart")

        return True, {"s_id": s_id, "destination": "10.30.0.179"}


    def request_slice(self, **kwargs):
       # Extract parameters from keyword arguments
       s_id = kwargs.get('s_id', None)

       # Return state
       return True, {s_id: {"start": 0, "end": 9, "length": 10}}


    def update_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Return state
        return True, "This is a stub"


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Return state
        return True, {"s_id": s_id}


if __name__ == "__main__":
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the OpenWiFi Controller
        opw_controller_thread = opw_controller(
            name='OpenWiFi',
            req_header='opw_req',  # Don't modify
            rep_header='opw_rep',  # Don't modify
            create_msg='owc_crs',
            request_msg='owc_rrs',
            update_msg='owc_urs',
            delete_msg='owc_drs',
            do_modules=False,
            do_network=False,
            do_ap=False,
            host='0.0.0.0',
            port=3100)

        # Start the OpenWiFi Controller Server
        opw_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the OpenWiFi Controller Server
        opw_controller_thread.safe_shutdown()
