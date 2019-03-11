#!/bin/env python3
# Import the path methods from the OS module
from os import path, killpg, setsid, getpgid
# Import the bash function from the bash module
from bash import bash

import signal
from subprocess import Popen, PIPE


class managed_process(object):
    # The process PID
    p_id = None

    # Spawn an external process
    def __init__(self, cmd):
        # Check for the type of variable
        if not isinstance(cmd, list):
            print('\t- Wrong argument type, not a list')
            raise Exception

        print(" ".join(cmd))
        print(cmd)

        return
        # Create the subprocess and add session ID to the parent
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, preexec_fn=setsid)

        # Check if it abruptly exited
        if not process.poll() is None:
            print('\t- Process failed abruptly.')
            raise Exception

        # Get the group process ID to kill everything
        self.process = process
        self.p_id = getpgid(process.pid)

    # Stop the process group
    def halt(self, **kwargs):
        # Kill the process and all it's child processes
        killpg(self.p_id, signal.SIGTERM)

    # Called upon garbage collection
    def __del__(self):
        if self.p_id is not None:
            self.halt()


class grc_manager(object):
    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        #  sdr_pool_path = kwargs.get('sdr_path', 'sdr_pool/')
        rat_pool_path = kwargs.get('rat_path', 'rat_pool/')

        #  SDR backend parameters
        #  sdr_tx = kwargs.get('tx', 'zmq_tx_usrp_script.py')
        #  sdr_rx = kwargs.get('rx', 'zmq_rx_usrp_script.py')
        #  sdr_trx = kwargs.get('trx', 'zmq_trx_usrp_script.py')

        tuntap_rat = 'tan_trx_xvl.py'
        self.rat_path = path.abspath(path.join(rat_pool_path, tuntap_rat))

        #  rat_tx = kwargs.get('rat_tx', 'tan_tx_zmq.py')
        #  rat_rx = kwargs.get('rat_rx', 'tan_rx_zmq.py')
        #  rat_trx = kwargs.get('rat_trx', 'tan_trx_zmq_script.py')

        #  RAT frontend parameters
        #  lte = kwargs.get('lte', 'lte')
        #  iot = kwargs.get('iot', 'iot')

        #  Calculate the absolute path to the RAT scripts
        #  self.rat_path = {
        #  'lte': {
        #  'tx': path.abspath(path.join(rat_pool_path, lte, rat_tx)),
        #  'rx': path.abspath(path.join(rat_pool_path, lte, rat_rx)),
        #  'trx': path.abspath(path.join(rat_pool_path, lte, rat_trx)),
        #  },
        #  'iot': {
        #  'tx': path.abspath(path.join(rat_pool_path, iot, rat_tx)),
        #  'rx': path.abspath(path.join(rat_pool_path, iot, rat_rx)),
        #  'trx': path.abspath(path.join(rat_pool_path, iot, rat_trx)),
        #  }
        #  }

        # Container to hold the RAT GRC processes
        self.rat_pool = {}

        # TODO find a better way to deal with the counter
        self.rat_counter = {1: False, 2: False}  #, 3: False, 4: False}

        # Calculate the absolute path to the SDR scripts
        #  self.sdr_path = {
        #  'tx': path.abspath(path.join(sdr_pool_path, sdr_tx)),
        #  'rx': path.abspath(path.join(sdr_pool_path, sdr_rx)),
        #  'trx': path.abspath(path.join(sdr_pool_path, sdr_trx))
        #  }

        # Container to hold the SDR GRC processes
        #  self.sdr_pool = {}

        # Current operation mode
        #  self.operation_mode = ''

    def _uhd_find_devices(self):
        # Try to locate uhd_find_devices binary
        where_uhd_find_devices = bash(
            'whereis uhd_find_devices').value().split(' ')

        # If the 'whereis' command didn't return any path to the binary
        if (len(where_uhd_find_devices) <= 1):
            #  Deifne error message
            msg = 'Cannot find \'uhd_find_devides\'.' + \
              'Are the UHD drivers installed?'
            # Throw error
            raise RuntimeError(msg)

        # Invoke uhd_find_devices
        # a = bash('/usr/bin/uhd_images_downloader').value()
        find_devices_stdout = bash(where_uhd_find_devices[1])

        # Sanitize the output
        usrp_list = [[
            entry.strip() for entry in usrp.split('\n')[1:]
        ] for usrp in [
            line.strip()
            for line in find_devices_stdout.value().split(50 * '-')[1:]
            if line != '\n'
        ][1::2]]

        # Convert the list of lists into a list of dictionaries
        usrp_dict = [dict(x.split(': ') for x in usrp) for usrp in usrp_list]

        return usrp_dict

    def _update_mode(self):
        # Create a set of the direction of the current SDRs
        temp = set((self.sdr_pool[sdr]['direction'] for sdr in self.sdr_pool))
        # Check if operating as a transceiver
        temp = set(('trx', )) if temp.issuperset(set(('rx', 'tx'))) else temp
        # Update the operation mode
        self.operation_mode = temp.pop() if temp else ''

    def create_rat(self, **kwargs):
        # Container to hold RAT configuration
        config = {}
        # Extract parameters from keyword arguments
        # config["freq"] = kwargs.get('centre_freq', 2e9) # UNUSED
        # config["gain"] = kwargs.get('norm_gain', 1) # UNUSED
        tech = kwargs.get('technology', 'lte')
        dirx = kwargs.get('direction', ' trx')
        s_id = kwargs.get('service_id', None)

        #  config["source_ip"] = kwargs.get(
        #  'source_ip', '127.0.0.1')
        #  config["source_port_suffix"] = kwargs.get(
        #  'source_port_suffix', 501)
        #  config["destination_ip"] = kwargs.get(
        #  'destination_ip', '127.0.0.1')
        #  config["destination_port_suffix"] = kwargs.get(
        #  'destination_port_suffix', 201)
        #  config["packet_len"] = kwargs.get(
        #  'packet_len', 84)

        # Sanitize input
        if s_id is None:
            raise Exception('Missing Service ID')

        # Check if the underlying USRP uses a supported operation mode
        #  if (config['dirx'] != self.operation_mode) or \
        #  (self.operation_mode != 'trx'):
        #  raise Exception('Invalid operation mode: ' + str(config['dirx']))

        # Check if we have free space left
        free_space = False
        for x in self.rat_counter:
            # If a slot is free
            if not self.rat_counter[x]:
                # Toggle the free space flag
                free_space = True
                break

        if not free_space:
            raise Exception('No bandwidth left to allocate the virtual radio')

        # Hold the RAT ID
        rat_id = x

        # System centre freq
        centre_freq = 3.75e9
        # Desired GB
        guard_band = 0.5e6
        # Desired Samp rate per channel
        samp_rate = 2e6
        # Offset between channels
        dist = 0.5 * (guard_band + samp_rate)
        # Total BW
        vr_bw = dist * 2
        # Bandwidth of the RF front-end
        rr_bw = 10e6
        # Centre the virtua; radio at the right place
        vr_cf = centre_freq - (0.5 * rr_bw) + (rat_id - 0.5) * vr_bw

        print('rr_cf', centre_freq)
        print('rr_bw', rr_bw)
        print('beggining', centre_freq - 0.5 * rr_bw)

        # Construct command arguments
        cmd = [
            self.rat_path, '--tx_offset', ' -' + str(dist), '--rx_offset',
            ' +' + str(dist), '--samp_rate',
            str(samp_rate), '--centre_frequency',
            str(vr_cf), '--rat_id',
            str(rat_id)
        ]

        # Create process
        try:
            process = managed_process(cmd)

        except Exception as e:
            # Check the process failed
            print(e)
            raise Exception('Failed Creating Radio Stack.')

        # Get hold of it
        self.rat_counter[rat_id] = True

        # If succeeded, append to RAT pool
        self.rat_pool[s_id] = {
            'tech': tech,
            'rat_id': rat_id,
            'process': process
        }

        print('- Created RAT')
        print('\t', 'Service ID:', s_id)
        print('\t', 'RAT ID:', rat_id)
        print('\t', 'Centre Frequency:', vr_cf)
        print('\t', 'Bandwidth:', vr_bw)
        print('\t', 'TX Channel:', vr_cf - dist)
        print('\t', 'RX Channel:', vr_cf + dist)

        # Return the RAT ID
        return rat_id

    def create_sdr(self, **kwargs):
        # Container to hold USRP configuration
        config = {}
        # Extract parameters from keyword arguments
        config["dirx"] = kwargs.get('direction', 'trx')

        config["ip"] = kwargs.get('ip', '127.0.0.1')
        config["source_port"] = kwargs.get('source_port', 201)
        config["destination_port"] = kwargs.get('destination_port', 501)
        config["port_offset"] = kwargs.get('port_offset', 0)
        config["serial"] = kwargs.get('serial', "")

        config["rate_tx"] = kwargs.get('samp_rate_tx', 1e6)
        config["rate_rx"] = kwargs.get('samp_rate_rx', 1e6)
        config["freq_tx"] = kwargs.get('centre_freq_tx', 2e9 - 1e6)
        config["freq_rx"] = kwargs.get('centre_freq_rx', 2e9 + 1e6)
        config["gain_tx"] = kwargs.get('gain_tx', 1)
        config["gain_rx"] = kwargs.get('gain_rx', 1)

        # If there's no serial
        if not config["serial"]:
            # Get the serial of an existing USRP
            print('- Findind USRP')
            found = self._uhd_find_devices()

            if not found:
                raise Exception('USRP not found.')

            else:
                config["serial"] = found[0]['serial']

        # Construct command arguments
        cmd = [
            self.sdr_path[config["dirx"]], '--ip', config["ip"],
            '--source_port',
            str(config["source_port"]), '--destination_port',
            str(config["destination_port"]), '--port_offset',
            str(config["port_offset"]), '--serial', config["serial"],
            '--samp_rate_tx',
            str(config["rate_tx"]), '--samp_rate_rx',
            str(config["rate_rx"]), '--centre_freq_rx',
            str(config["freq_rx"]), '--centre_freq_tx',
            str(config["freq_tx"]), '--gain_tx',
            str(config["gain_tx"]), '--gain_rx',
            str(config["gain_rx"])
        ]

        try:
            # Create process
            process = managed_process(cmd)

        except Exception as e:
            # Check the process failed
            raise Exception('Failed interfacing with the USRP.')

        # If succeeded, append to SDR GRC pool
        self.sdr_pool[config["serial"]] = {
            'direction': config["dirx"],
            'process': process
        }

        # Update the operation mode
        self._update_mode()

        print('- Created SDR')
        for item in config:
            print('\t-' + item + ": " + str(config[item]))

    def remove_rat(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', '')

        print('- Removing RATs')
        # Iterate over the list of current processes
        for service_id in list(self.rat_pool.keys()):
            # If a RAT matches the RAT s_id or we should remove all RATs
            if service_id == s_id or not s_id:
                # Kill the RAT process and all it's child processes
                self.rat_pool[service_id]['process'].halt()
                print('\t- Removed RAT: ' + service_id)

                # Clear the RAT counter
                self.rat_counter[self.rat_pool[service_id]['rat_id']] = False

                # If there's no specific Service ID
                if not s_id:
                    # Remove it from the SDR pool
                    self.rat_pool.pop(service_id)

                # Otherwise
                else:
                    # Remove the RAT and return its RAT ID
                    return self.rat_pool.pop(service_id)['rat_id']

    def remove_sdr(self, **kwargs):
        # Extract parameters from keyword arguments
        serial = kwargs.get('serial', '')

        print('- Removing USRPs')
        # Iterate over the list of current processes
        for sdr_id in list(self.sdr_pool.keys()):
            # If a SDR matches the SDR serial or we should remove all SDRs
            if sdr_id == serial or not serial:
                # Kill the SDR process and all it's child processes
                self.sdr_pool[sdr_id]['process'].halt()
                print('\t- Removed SDR: ' + sdr_id)
                # Remove it from the SDR pool
                self.sdr_pool.pop(sdr_id)
                # Update the operation mode
                self._update_mode()


if __name__ == "__main__":
    print(0)
