#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the ArgParse modeule
import argparse

def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Manage E2E Services')
    # Add a conflicting argument group
    group = parser.add_mutually_exclusive_group(required=True)
    # Add CLI arguments
    group.add_argument(
    '-a', '--address',
    metavar='IPV4_SOURCE_ADDRESS',
    type=str,
    help='create a slicing with this source address')
    group.add_argument(
        '-s', '--service-id',
        metavar='S_ID',
        help='remove a service based on its S_ID')
    parser.add_argument(
        '-q', '--qos',
        nargs='+',
        metavar=('KEY=VALUE'),
        help='require a QoS-based slicing. Current supported keys are latency (ms) and throughput (Mb), e.g. --qos latency=1 throughput=1')

    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    # Generate QoS dictionary 
    if arg_dict.get('qos') is not None:
        qos = {}
        for param in arg_dict.get('qos'):   
            if "=" in param:
                key_value = param.split('=')
                qos[key_value[0]] = float(key_value[1])
        arg_dict['qos'] = qos

    return arg_dict


def establish_connection(**kwargs):
    # Default RU Server host
    host = kwargs.get('host', '10.0.0.3')
    # Default RU Server port
    port = kwargs.get('port', 1100)

    # Create a ZMQ context
    context = zmq.Context()
    #  Specity the type of ZMQ socket
    socket = context.socket(zmq.REQ)
    # Connect ZMQ socket to host:port
    socket.connect("tcp://" + host + ":" + str(port))

    return socket


def service_request(socket, **kwargs):

    create_msg = 'sr_cs'
    create_ack = 'cs_ack'
    create_nack = 'cs_nack'

    # TODO: we need to remove traffic_type from here. I let it just to test the changes in the wired orch...
    traffic_type = 'low-latency'
    #traffic_type = 'high-throughput'
    
    # Send service request message to the hyperstrator
    socket.send_json({create_msg: {'address': kwargs['address'], 
                                  'qos': kwargs['qos'],
                                  'type': traffic_type
                                  }})
    
    # Receive acknowledgment
    rep = socket.recv_json()

    # Check if there's an acknowledgment
    ack = rep.get(create_ack, None)

    # If received an acknowledgement
    if ack is not None:
        print('- Created Service:')
        # Print information
        print('\tService ID:', ack['s_id'], '\n',
              '\tHost:', ack['host'])

        # Exit gracefully
        exit(0)


    # Check if there's a not acknowledgement
    nack = rep.get(create_nack, None)

    # If received a not acknowledgement
    if nack is not None:
        print('- Failed to create service.')
        # Print reason
        print('\tReason: ', nack)
        # Opsie
        exit(0)

    # If neither worked
    if (ack is None) and (nack is None):
        print('- Failed to parse message:')
        print('\tMessage:', rep)


def service_release(socket, **kwargs):

    delete_msg = "sr_ds"
    delete_ack = "ds_ack"
    delete_nack = "ds_nack"

    # Send service release messate to the hyperstrator
    socket.send_json({delete_msg: {'s_id': kwargs['service_id']}})
    # Receive acknowledgment
    rep = socket.recv_json()

    # Check if there's an acknowledgement
    ack = rep.get(delete_ack, None)

    # If received an acknowledgement
    if ack is not None:
        print('- Removed Service:')
        # Print information
        print('\tService ID:', ack['s_id'])
        # Exit gracefully
        exit(0)

    # Check if there's a not acknowledgement
    nack = rep.get(delete_nack, None)

    # If received a not acknowledgement
    if nack is not None:
        print('- Failed to remove service.')
        # Print reason
        print('\tReason: ', nack)
        # Opsie
        exit(0)

    # If neither worked
    if (ack is None) and (nack is None):
        print('- Failed to parse message:')
        print('\tMessage:', rep)


if __name__ == "__main__":
    # Parse CLI arguments
    kwargs = parse_cli_args()
    # Establish connection to the RU Server
    socket = establish_connection()

    # If not passing a service ID
    if kwargs['service_id'] is None:
        # Request new E2E service
        service_request(socket, **kwargs)
    # Otherwise
    else:
        # Release an E2E service
        service_release(socket, **kwargs)
