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

    def __init__(self, cmd):
        # Check for the type of variable
        if not isinstance(cmd, list):
            print('\t- Wrong argument type, not a list')
            raise Exception

        # Create the subprocess and add session ID to the parent
        process = Popen(
            cmd, stdout=PIPE, stderr=PIPE, preexec_fn=setsid)

        # Check if it abruptly exited
        if not process.poll() is None:
            print('\t- Process failed abruptly.')
            raise Exception

        # Get the group process ID to kill everything
        self.process = process
        self.p_id = getpgid(process.pid)

    def halt(self, **kwargs):
        # Kill the process and all it's child processes
        killpg(self.p_id, signal.SIGKILL)


class grc_manager(object):
    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        rat_pool = kwargs.get('rat_path', 'rat_pool/')
        sdr_pool = kwargs.get('sdr_path', 'sdr_pool/')

        # RAT frontend parameters
        lte = kwargs.get('lte', 'udp_lte_zmq_script.py')
        iot = kwargs.get('iot', 'udp_iot_zmq_script.py')

        # SDR backend parameters
        tx = kwargs.get('tx', 'zmq_usrp_sink_script.py')
        rx = kwargs.get('rx', 'zmq_usrp_source_script.py')
        trx = kwargs.get('trx', 'zmq_usrp_both_script.py')

        # Calculate the absolute path to the RAT scripts
        self.rat_path = {
            'lte': path.abspath(path.join(rat_pool, lte)),
            'iot': path.abspath(path.join(rat_pool, iot))
        }

        # Container to hold the RAT GRC processes
        self.rat_pool = []

        # Calculate the absolute path to the SDR scripts
        self.sdr_path = {
            'tx': path.abspath(path.join(sdr_pool, tx)),
            'rx': path.abspath(path.join(sdr_pool, rx)),
            'trx': path.abspath(path.join(sdr_pool, trx))
        }

        # Container to hold the SDR GRC processes
        self.sdr_pool = []

    def uhd_find_devices(self):
        # Try to locate uhd_find_devices binary
        where_uhd_find_devices = bash(
            'whereis uhd_find_devices').value().split(' ')

        # If the 'whereis' command didn't return any path to the binary
        if (len(where_uhd_find_devices) <= 1):
            #  Deifne error message
            msg = 'Cannot find \'uhd_find_devides\'.' + \
              'Are the UHD drivers installed?'
            # Throw error
            throw_error(RuntimeError, msg)

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

    def create_rat(self, **kwargs):
        # Container to hold the configuration
        config = {}
        # Extract parameters from keyword arguments
        config["freq"] = kwargs.get('centre_freq', 2e9)
        config["gain"] = kwargs.get('norm_gain', 1)
        config["tech"] = kwargs.get('technology', 'lte')

        config["host"] = kwargs.get('host', '0.0.0.0')
        config["port"] = kwargs.get('port', 6000)
        config["zmq"] = kwargs.get('zmq', 9000)

        # Append the ZMQ address and protocol type to the ZMQ port
        config["zmq"] = 'tcp://127.0.0.1:' + str(config["zmq"])

        # Contruct command arguments
        cmd = [
            self.rat_path[config["tech"]], '--freq',
            str(config["freq"]), '--gain',
            str(config["gain"]), '--subdev', 'A:A', '--port',
            str(config["port"]), '--ip', config["host"], '--zmq', config["zmq"]
        ]

        # Create process
        try:
            process = managed_process(cmd)

        except:
            # Check the process failed
            return False

        # If succeeded, append to RAT pool
        self.rat_pool.append({'tech': config["tech"], 'process': process})

        print('- Created RAT')
        for x in config:
            print('\t-' + x + ": " + str(config[x]))
            return True

    def create_sdr(self, **kwargs):
        # Container to hold the configuration
        config = {}
        # Extract parameters from keyword arguments
        config["freq"] = kwargs.get('centre_freq', 2e9)
        config["rate"] = kwargs.get('samp_rate', 1e6)
        config["gain"] = kwargs.get('norm_gain', 1)
        config["dirt"] = kwargs.get('direction', 'tx')

        config["host"] = kwargs.get('host', '127.0.0.1')
        config["port"] = kwargs.get('port', 6000)
        config["usrp"] = kwargs.get('serial', '')

        # If there's now serial
        if not config['usrp']:
            # Get the serial of an existing USRP
            print('- Findind USRP')
            found = self.uhd_find_devices()

            if not found:
                print('\t- USRP not found.')
                return False

            else:
                config["usrp"] = found[0]['serial']

        # Contruct command arguments
        cmd = [
            self.sdr_path[config["dirt"]], '--freq',
            str(config["freq"]), '--rate',
            str(config["rate"]), '--gain',
            str(config["gain"]), '--subdev', 'A:A', '--port',
            str(config["port"]), '--ip', config["host"], '--usrp',
            '\'serial=' + config["usrp"] + '\''
        ]

        try:
            # Create process
            process = managed_process(cmd)

        except:
            # If it failed
            return False

        # If succeeded, append to SDR GRC pool
        self.sdr_pool.append({'serial': config["usrp"], 'process': process})

        print('- Created SDR')
        for x in config:
            print('\t-' + x + ": " + str(config[x]))

    def remove_rat(self, **kwargs):
        # Extract parameters from keyword arguments
        serial = kwargs.get('serial', '')

        print('- Removing RATs')
        # Iterate over the list of current processes
        for rat in self.rat_pool[:]:
            # If a RAT matches the RAT s_id or we should remove all RATs
            if rat['serial'] == serial or not serial:
                # Kill the RAT process and all it's child processes
                rat['process'].halt()
                print('\t- Removed RAT: ' + rat['serial'])
                # Remove it from the SDR pool
                self.rat_pool.remove(rat)

    def remove_sdr(self, **kwargs):
        # Extract parameters from keyword arguments
        serial = kwargs.get('serial', '')

        print('- Removing SDRs')
        # Iterate over the list of current processes
        for sdr in self.sdr_pool[:]:
            # If a SDR matches the USRP serial or we should remove all SDRs
            if sdr['serial'] == serial or not serial:
                # Kill the sdr process and all it's child processes
                sdr['process'].halt()
                print('\t- Removed USRP: ' + sdr['serial'])
                # Remove it from the SDR pool
                self.sdr_pool.remove(sdr)


# TODO RAT idenfifier
# TODO Unique RAT port

if __name__ == "__main__":
    print(0)
