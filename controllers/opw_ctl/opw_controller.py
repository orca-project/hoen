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
        bash("service network manager stop")
        self._log("Stopped Network Manager")

        # If loading kernel modules
        if do_modules:
            fpga_dev_path = "/sys/bus/iio/devices/iio:device2"

            # Load mac80211 kernel module
            a = bash("modprobe mac80211")
            self._log("Loaded 'mac80211' kernel module", a.stdout, a.stderr)

            # If the SDR kernel module is loaded
            if bool(bash("lsmod | grep sdr")):
                # Remove SDR kernel module
                a = bash("rmmod sdr")
                self._log("Removed 'sdr' kernel module", a)

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
                cf = "insmod {0}/{1}.ko".format(openwifi_path, submodule)
                print(cf)
                # Installing new version of the module
                b = bash(cf)
                # Check installation of kernel module
                sleep(1)
                if not bash("lsmod | grep {0}".format(submodule)).code:
                    self._log("Loaded", submodule, "kernel module")

                else:
                    self._log("Not loaded", submodule, "kernel module")
                print(submodule, b)

            for parameter in device_config["first_batch"].keys():
                # Update the parameter value
                cf = "echo {0} > {1}/{2}".format(
                         device_config["first_batch"][parameter],
                         fpga_dev_path,
                         parameter)
                print(cf)
                a = bash(cf)
                bash("sync")
                sleep(0.5)
                print(parameter, a.stdout, a.stderr)

            # Load filter response values
            a = bash("cat {0}/openwifi_ad9361_fir.ftr >" +
                 "{1}/filter_fir_config".format(openwifi_path, fpga_dev_path))

            print(a.stdout)

            for parameter in device_config["second_batch"].keys():
                # Update the parameter value
                cf = "echo {0} > {1}/{2}".format(
                    device_config["second_batch"][parameter],
                    fpga_dev_path,
                    parameter)
                print(cf)
                a = bash(cf)
                bash("sync")
                sleep(0.5)
                print(parameter, a.stdout, a.stderr)

            # Iterate over the second batch
            for submodule in module_list['second_batch']:
                # Check whether the module is loaded
                if bool(bash("lsmod | grep {0}".format(submodule))):
                    # Removing current version of the module
                    bash("rmmod {0}".format(submodule))

                cf = "insmod {0}/{1}.ko".format(openwifi_path, submodule)
                print(cf)
                # Installing new version of the module
                b = bash(cf)
                sleep(1)
                # Check installation of kernel module
                if not bash("lsmod | grep {0}".format(submodule)).code:
                    self._log("Loaded", submodule, "kernel module")

                print(submodule, b)

            # Sleep for 10 seconds and log event
            self._log("Waiting for configurations to take effect")
            sleep(20)
            self._log("Configured kernel modules and FPGA")

        # If configuring routing and networking
        if do_network:
            # Configure the SDR interface's IP
            a= bash("ifconfig {0} {1} netmask 255.255.255.0".format(sdr_dev,
                                                                 lan_ip))
            self._log("Set {0} interface IP's to: {1}".format(sdr_dev, lan_ip),
                      a.stdout, a.stderr)

            # Set the default route through eth0
            a = bash("ip route add default via {0} dev eth0".format(gw_ip))
            self._log("Set default gateway to: {0}".format(gw_ip), a.stdout,
                      a.stderr)

            # Restart DHCP server
            a = bash("service isc-dhcp-server restart")
            self._log("Restarted DHCP server", a.stdout, a.stderr)

            # Sleep for 5 seconds and log event
            sleep(10)
            self._log("Configured routing and networking")

        # If starting the access point
        if do_ap:
            # Start Host AP Daemon in the background and log event
            a = bash("hostapd -B {0}".format(ap_config_path))

            apd = a.code
            # Log event
            self._log(a.stdout, a.stderr, "Configured access point" if apd else \
                      "Access point not initialised.")



    def create_slice(self, **kwargs):
       # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))

        # Return state
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
            do_modules=True,
            do_network=True,
            do_ap=True,
            host='0.0.0.0',
            port=3100)

        # Start the OpenWiFi Controller Server
        opw_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the OpenWiFi Controller Server
        opw_controller_thread.safe_shutdown()
