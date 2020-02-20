#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the ArgParse modeule
import argparse

def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Manage E2E Services')
    # Create subparsers
    subparsers = parser.add_subparsers(help='Sub-command Help')

    # Create parser for the creation of slices
    parser_a = subparsers.add_parser(
        'create',
        help='Create E2E Network Slice',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Add CLI arguments
    parser_a.add_argument(
        '-s', '--source',
        metavar='IPV4_SOURCE_ADDRESS',
        type=str,
        default='127.0.0.1',
        #  required=True, # I wonder whether this arguments must be required
        help='Source Address')
    parser_a.add_argument(
        '-t', '--throughput',
        type=float,
        #default=1.0,
        help='Required throughput [Mbps]')
    parser_a.add_argument(
        '-l', '--latency',
        type=float,
        #default=10.0,
        help='Required latency [ms]')

    # Create parser for the removal of slices
    parser_b = subparsers.add_parser('remove', help='Remove E2E Network Slice')
    # Add CLI arguments
    parser_b.add_argument(
        '-i', '--service-id',
        metavar='S_ID',
        type=str,
        help='Remove service based on the S_ID')

    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    return arg_dict


def establish_connection(**kwargs):
    # Default RU Server host
    host = kwargs.get('host', '10.0.0.3')
    # Default RU Server port
    port = kwargs.get('port', 1100)

    # Create a ZMQ context
    context = zmq.Context()
    #  Specify the type of ZMQ socket
    socket = context.socket(zmq.REQ)
    # Connect ZMQ socket to host:port
    socket.connect("tcp://" + host + ":" + str(port))

    return socket


def service_request(socket, **kwargs):
    # Service Request - Create Slice
    create_msg = 'sr_cs'
    create_ack = 'cs_ack'
    create_nack = 'cs_nack'

    # Send service request message to the hyperstrator
    socket.send_json({
        create_msg: {'source': kwargs['source'],
                     #  'destination': kwargs['destination'],
                     'requirements': {'throughput': kwargs['throughput'],
                                      'latency': kwargs['latency']}
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
              '\tDestination:', ack['destination'])

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
    # Service Request - Delete Slice
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
    if 'service_id' not in kwargs:
        # Request new E2E service
        service_request(socket, **kwargs)
    # Otherwise
    else:
        # Release an E2E service
        service_release(socket, **kwargs)
