#!/bin/env python3
# Import the path methods from the OS module
from os import path, kill, setsid, getpgid
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

        #  print(" ".join(cmd))
        #  print(cmd)

        # Create the subprocess and add session ID to the parent
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, preexec_fn=setsid)

        # Check if it abruptly exited
        if not process.poll() is None:
            print('\t- Process failed abruptly.')
            raise Exception

        # Get the group process ID to kill everything
        self.process = process
        self.p_id = process.pid

    # Stop the process group
    def halt(self, **kwargs):
        # Kill the process and all it's child processes
        kill(self.p_id, signal.SIGKILL)
        self.process.communicate()

class grc_manager(object):
    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        #  sdr_pool_path = kwargs.get('sdr_path', 'sdr_pool/')
        rat_pool_path = kwargs.get('rat_path', 'rat_pool/')

        tuntap_rat = 'tan_trx_zmq.py'
        self.rat_path = path.abspath(path.join(rat_pool_path, tuntap_rat))

        # Container to hold the RAT GRC processes
        self.rat_pool = {}

    def create_rat(self, **kwargs):
        # Container to hold RAT configuration
        config = {}
        # Extract parameters from keyword arguments
        # config["freq"] = kwargs.get('centre_freq', 2e9) # UNUSED
        # config["gain"] = kwargs.get('norm_gain', 1) # UNUSED
        tech = kwargs.get('technology', 'lte')
        rat_id = kwargs.get('rat_id', 0)
        tx_port = kwargs.get('tx_port', 200)
        rx_port = kwargs.get('rx_port', 500)
        dirx = kwargs.get('direction', ' trx')
        s_id = kwargs.get('service_id', None)

        if tx_port in [1, '1']:
            tx_port = 6200

        if rx_port in [1, '1']:
            rx_port = 6500

        # Sanitize input
        if s_id is None:
            raise Exception('Missing Service ID')

        # Construct command arguments
        cmd = [
            self.rat_path,
            #  '--tx_offset', ' -' + str(dist),
            #  '--rx_offset', ' +' + str(dist),
            #  '--samp_rate',  str(samp_rate),
            #  '--centre_frequency', str(vr_cf),
            '--destination_port',
            str(tx_port),
            '--source_port',
            str(rx_port),
            '--rat_id',
            str(rat_id)
        ]

        # Create process
        try:
            process = managed_process(cmd)

        except Exception as e:
            # Check the process failed
            print(e)
            raise Exception('Failed Creating Radio Stack.')

        # If succeeded, append to RAT pool
        self.rat_pool[s_id] = {
            'tech': tech,
            'rat_id': rat_id,
            'process': process
        }

        print('- Created RAT')
        print('\t', 'Service ID:', s_id)
        print('\t', 'RAT ID:', rat_id)
        #  print('\t', 'Centre Frequency:', vr_cf)
        #  print('\t', 'Bandwidth:', vr_bw)
        #  print('\t', 'TX Channel:', vr_cf - dist)
        #  print('\t', 'RX Channel:', vr_cf + dist)

        # Return the RAT ID
        return process

    def remove_rat(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('service_id', '')

        print('- Removing RATs')
        # Iterate over the list of current processes
        for service_id in list(self.rat_pool.keys()):
            # If a RAT matches the RAT s_id or we should remove all RATs
            if service_id == s_id or not s_id:
                # Kill the RAT process and all it's child processes
                self.rat_pool[service_id]['process'].halt()
                print('\t- Removed RAT: ' + service_id)

                # If there's no specific Service ID
                if not s_id:
                    # Remove it from the SDR pool
                    self.rat_pool.pop(service_id)

                # Otherwise
                else:
                    # Remove the RAT and return its RAT ID
                    return self.rat_pool.pop(service_id)['rat_id']
