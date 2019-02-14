#!/bin/env python3
# Import the bash function from the bash module
from bash import bash
# Import the sleep function from the time module
from time import sleep

class route_manager(object):

    def __init__(self):
        # TODO maybe keep a collection of current routes?
        pass

    def create_route(self, **kwargs):
        # Extract parameters from keyword arguments
        rat_id = kwargs.get('rat_id', None)

        # Check if the rat_id is missing
        if rat_id is None:
            raise Exception('Missing RAT ID')

        # Based on the RAT ID, construct the IP address and interface name
        ip = f'10.0.{rat_id}.1'
        interface = f'tap{rat_id}'

        # Wait for a second while the TAP interface starts
        sleep(1)

        # Print info message
        print('- Establishing routes')

        # Configure the TAP interface
        bash(f'ifconfig {interface} {ip}')
        # Print info message
        print('\tConfigured interface: ' + interface)

        # Configure the route
        bash(f'ip route add 10.0.{rat_id}.0/24 via {ip} dev {interface}')
        # Print info message
        print('\tConfigured route through: ' + ip)

        # Return the interface's IP
        return ip

    def remove_route(self, **kwargs):
        # Extract parameters from keyword arguments
        rat_id = kwargs.get('rat_id', None)

        # Check if the rat_id is missing
        if rat_id is None:
            raise Exception('Missing RAT ID')

        # Based on the RAT ID, construct the IP address and interface name
        ip = f'10.0.{rat_id}.1'
        interface = f'tap{rat_id}'

        # Print info message
        print('- Removing routes')

        # Configure the route
        bash(f'ip route del 10.0.{rat_id}.0/24 via {ip} dev {interface}')

        # Print info message
        print('\tRemoved route through: ' + ip)
