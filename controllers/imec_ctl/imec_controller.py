#!/usr/bin/env python3

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import OS
import os
# Import signal
import signal

# Import subprocess to execute commands
from subprocess import call, Popen, PIPE, check_output, STDOUT

# iw executable path
iw_exec = "/root/iw/iw"

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


class imec_controller(base_controller):

    def post_init(self, **kwargs):
        # TODO Override this method at will
        print('- Starting IMEC Controller')

        # start an adhoc network
        # Get adhoc parameters from keyword arguments
        self.adhoc_iface   = kwargs.get('adhoc_iface', 'sdr0')
        self.adhoc_essid   = kwargs.get('adhoc_essid', 'sdr-ad-hoc')
        self.adhoc_channel = kwargs.get('adhoc_channel', 8)
        self.adhoc_ip      = kwargs.get('adhoc_ip', '192.168.13.20')
        self.adhoc_net     = kwargs.get('adhoc_net', '192.168.13.0')
        self.adhoc_mask    = kwargs.get('adhoc_mask', '255.255.255.0')

#        # Bring interface down
#        call(['ifconfig', self.adhoc_iface, 'down'])
#        # Change interface mode
#        call(['iwconfig', self.adhoc_iface, 'mode', 'ad-hoc'])
#        # Select essid
#        call(['iwconfig', self.adhoc_iface, 'essid', self.adhoc_essid])
#        # Bring interface up
#        call(['ifconfig', self.adhoc_iface, 'up'])
#        # Configure channel
#        call(['iwconfig', self.adhoc_iface, 'channel', str(self.adhoc_channel)])
#        # Configure ip address
#        call(['ifconfig', self.adhoc_iface, self.adhoc_ip, 'netmask', self.adhoc_mask])

        # Remove any routing entry using adhoc interface
        call(['route', 'del', '-net', self.adhoc_net, 'netmask', self.adhoc_mask, 'dev', self.adhoc_iface])

        # Create a slice dictionary instance
        self.s_dict = {}

    def set_radio_slice(self, command, value):

        # Execute radio slice command
        p = Popen([iw_exec, 'dev', self.adhoc_iface, 'set', command, value], stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()

        if len(err) == 0:
           # Retrieve configured radio slice parameter
            p = Popen([iw_exec, 'dev', self.adhoc_iface, 'get', command], stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()

            if len(err) == 0:
                value_new = output.decode("utf-8").split(':')[1].strip().strip('us')
                if value_new == value:
                    msg = {'nl_ack': 'success'}
                else:
                    msg = {'nl_nack': command + ' = ' + value + ' is not set correctly'}
            else:
                msg = {'nl_nack': err.decode("utf-8")}

        else:
            msg = {'nl_nack': err.decode("utf-8")}

        return msg

    def pre_exit(self):
     # Terminate the IMEC SDR Controller Server
        self.shutdown_flag.set()
        # Join thread
        self.join()

    def create_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Check availability of a resource slice
        if len(self.s_dict) >= 2:
            return False, 'Slice resource not available'

        # Retrieve list of IP/MAC addresses, that are part of the adhoc network
        #dest_IPs  = check_output("arp -an | grep sdr0 | cut -d '(' -f2 | cut -d ')' -f1", shell=True, stderr=STDOUT).decode("utf-8").strip().split('\n')
        #dest_MACs = check_output("arp -an | grep sdr0 | cut -d ' ' -f4", shell=True, stderr=STDOUT).decode("utf-8").strip().split('\n')
        dest_IPs  = ["192.168.13.15", "192.168.13.25"]
        dest_MACs = ["00:c0:ca:84:63:6a", "64:70:33:04:4a:bf"]

        # Pick a terminal, that has no slice assigned for
        for i in range(len(dest_IPs)):
            if dest_IPs[i] not in self.s_dict.values():

                # Map service id to IP address
                self.s_dict[s_id] = dest_IPs[i]

                # Update the routing table to include the newly registered node
                call(['route', 'add', '-net', dest_IPs[i], 'netmask', '255.255.255.255', 'dev', self.adhoc_iface])

                # Calculate low32 (in hex) from destination MAC address
                dest_MAC = dest_MACs[i].split(':')
                dest_MAC_4oct = ''.join(dest_MAC[-4:])

                # Configure slice
                msgs = {}
                if len(self.s_dict) == 1:
                    # low latency supported slice
                    msgs['addr']  = self.set_radio_slice('addr0', dest_MAC_4oct)
#                    msgs['total'] = self.set_radio_slice('slice_total0', '50000')
#                    msgs['start'] = self.set_radio_slice('slice_start0', '0')
#                    msgs['end']   = self.set_radio_slice('slice_end0', '50000')

                else:
                    # duty cycle supported slice
                    msgs['addr']  = self.set_radio_slice('addr1', dest_MAC_4oct)
#                    msgs['total'] = self.set_radio_slice('slice_total1', '25000')
#                    msgs['start'] = self.set_radio_slice('slice_start1', '1000')
#                    msgs['end']   = self.set_radio_slice('slice_end1', '2000')

                # Check for error messages
                error_msg = ""
                for key, value in msgs.items():
                    if 'nl_nack' in msgs[key]:
                        error_msg = error_msg + "\n" + msgs[key]['nl_nack']

                if error_msg != "":
                    # Revert back routing and dictionary updates
                    call(['route', 'del', '-net', dest_IPs[i], 'netmask', '255.255.255.255', 'dev', self.adhoc_iface])
                    self.s_dict.pop(s_id)

                    return False, error_msg
                else:
                    return True, {'host': dest_IPs[i]}

        return False, 'Terminal device not available'


    def delete_slice(self, **kwargs):
        # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Retrieve destination IP from service id to IP dictionary
        dest_IP = self.s_dict.pop(s_id)

        # Update the routing table to remove the registered node
        call(['route', 'del', '-net', dest_IP, 'netmask', '255.255.255.255', 'dev', self.adhoc_iface])

        # Return the radio slice information
        return True, {'s_id': s_id}


if __name__ == "__main__":
    # Clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the IMEC SDR Controller
        imec_controller_thread = imec_controller(
            name='IMEC',
            req_header='imec_req', # Don't modify
            rep_header='imec_rep', # Don't modify
            create_msg='wlc_crs',
            request_msg='wlc_rrs',
            update_msg='wlc_urs',
            delete_msg='wlc_drs',
            host='10.2.0.1',
            port=6000,
            adhoc_iface='sdr0',
            adhoc_essid='sdr-ad-hoc',
            adhoc_channel='1',
            adhoc_ip='192.168.13.20',
            adhoc_net='192.168.13.0',
            adhoc_mask='255.255.255.0')

        # Start the IMEC SDR Controller Server
        imec_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the IMEC SDR Controller Server
        imec_controller_thread.pre_exit()

        print('Exiting')
