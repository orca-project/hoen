#!/bin/env python3
# Import the path methods from the OS module
from os import path, killpg, setsid, getpgid

from subprocess import Popen, PIPE


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


    def create_rat(self, **kwargs):
        # Extract parameters from keyword arguments
        freq = kwargs.get('centre_freq', 2e9)
        gain = kwargs.get('norm_gain', 1)
        tech = kwargs.get('technology', 'lte')

        host = kwargs.get('host', '0.0.0.0')
        port = kwargs.get('port', 6000)
        zmq = kwargs.get('zmq', 9000)

        # Append the ZMQ address and protocol type to the ZMQ port
        zmq = 'tcp://127.0.0.1:' + str(zmq)

        # Contruct command arguments
        cmd = [self.rat_path[tech],
               '--freq', str(freq),
               '--gain', str(gain),
               '--subdev', 'A:A',
               '--port', str(port),
               '--ip', host,
               '--zmq', zmq]

        print(' '.join(cmd))
        # Try to create the RAT process
        try:
            # Create the RAT with subprocess and add session ID to the parent
            rat_process = Popen(' '.join(cmd),
                                shell=True,
                                stdout=PIPE,
                                stderr=PIPE,
                                preexec_fn=setsid)
            # Update the process status
            (out,err) = rat_process.communicate()

            # Script not found
            if rat_process.returncode == 127:
                print('Could not find script: ' + str(self.rat_path[tech]))
                exit(10)

        except Exception as e:
            print('Failed creating RAT process.')
            exit(10)

        else:
            # If succeeded, append to SDR pool
            self.rat_pool.append({'tech': tech, 'process': rat_process})

        print('- Created RAT')
        print(kwargs)



    def create_sdr(self, **kwargs):
        # Extract parameters from keyword arguments
        freq = kwargs.get('centre_freq', 2e9)
        rate = kwargs.get('samp_rate', 1e6)
        gain = kwargs.get('norm_gain', 1)
        dirt = kwargs.get('direction', 'tx')

        host = kwargs.get('host', '127.0.0.1')
        port = kwargs.get('port', 6000)
        usrp = kwargs.get('serial', '')

        # Contruct command arguments
        cmd = [self.sdr_path[dirt],
               '--freq', str(freq),
               '--rate', str(rate),
               '--gain', str(gain),
               '--subdev', 'A:A',
               '--port', str(port),
               '--ip', host,
               '--usrp', '\'serial=' + usrp + '\'']

        # Try to create the SDR process
        try:
            # Create the SDR with subprocess and add session ID to the parent
            sdr_process = Popen(' '.join(cmd),
                                shell=True,
                                stdout=PIPE,
                                stderr=PIPE,
                                preexec_fn=setsid)

        except Exception as e:
            print('Failed creating SDR process.')
            exit(10)

        else:
            # If succeded, append to SDR GRC pool
            self.sdr_pool.append({'serial': usrp, 'process': sdr_process})

        print('- Created SDR')
        print(kwargs)


    def remove_rat(self, **kwargs):
        # Extract parameters from keyword arguments
        serial = kwargs.get('serial', '')

        # Iterate over the list of current processes
        for rat in self.rat_pool[:]:
            # If a SDR matches the USRP serial
            if rat['serial'] == serial:
                # Kill the sdr process and all it's child processes
                killpg(getpgid(rat['process'].pid), signal.SIGKILL)

                # Remove it from the SDR pool
                self.rat_pool.remove(rat)

        print('- Removed RAT')
        print(kwargs)

    def remove_sdr(self, **kwargs):
        # Extract parameters from keyword arguments
        serial = kwargs.get('serial', '')

        # Iterate over the list of current processes
        for sdr in self.sdr_pool[:]:
            # If a SDR matches the USRP serial
            if sdr['serial'] == serial:
                # Kill the sdr process and all it's child processes
                killpg(getpgid(sdr['process'].pid), signal.SIGKILL)

                # Remove it from the SDR pool
                self.sdr_pool.remove(sdr)

        print('- Removed SDR')
        print(kwargs)

# TODO RAT idenfifier
# TODO Unique RAT port

if __name__ == "__main__":
    print(0)
