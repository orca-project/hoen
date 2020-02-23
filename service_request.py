#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the ArgParse modeule
import argparse

def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Manage E2E Services')
    # Create subparsers
    subparsers = parser.add_subparsers(help='Sub-command Help',
                                       dest='subcommand')
    # Require subcommands
    subparsers.required = True

    # Create parser for the creation of slices
    parser_a = subparsers.add_parser(
        'create',
        help='Create a new E2E Network Slice',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Add CLI arguments
    parser_a.add_argument(
        '-d', '--distro',
        metavar='Type of Linux Distribution',
        type=str,
        default='ubuntu-19.04-plain',
        #  required=True, # I wonder whether this arguments must be required
        help='Source Address')
    parser_a.add_argument(
        '-t', '--throughput',
        type=float,
        default=1.0,
        help='Required throughput [Mbps]')
    parser_a.add_argument(
        '-l', '--latency',
        type=float,
        default=10.0,
        help='Required latency [ms]')

    # Create parser for the removal of slices
    parser_b = subparsers.add_parser(
        'delete',
        help='Remove an existing E2E Network Slice')

    # Add CLI arguments
    parser_b.add_argument(
        '-i', '--service-id',
        metavar='S_ID',
        type=str,
        required=True,
        help='Remove service based on the S_ID')

    # Create parser for the getting information about the slices
    parser_c = subparsers.add_parser(
        'request',
        help='Request information about  E2E Network Slice')

    # Add CLI arguments
    parser_c.add_argument(
        '-i', '--service-id',
        metavar='S_ID',
        type=str,
        required=True,
        help='Request information on service based on the S_ID')

    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    return arg_dict


def establish_connection(**kwargs):
    # Default RU Server host
    host = kwargs.get('host', '127.0.0.1')
    # Default RU Server port
    port = kwargs.get('port', 1100)

    # Create a ZMQ context
    context = zmq.Context()
    #  Specify the type of ZMQ socket
    socket = context.socket(zmq.REQ)
    # Connect ZMQ socket to host:port
    socket.connect("tcp://" + host + ":" + str(port))

    return socket


def service_create(socket, **kwargs):
    # Service Request - Create Slice
    create_msg = 'sr_cs'
    create_ack = 'cs_ack'
    create_nack = 'cs_nack'

    # Send service request message to the hyperstrator
    socket.send_json({
        create_msg: {'distribution': kwargs['distro'],
                     'requirements': {'throughout': kwargs['throughput'],
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
        print('\tService ID:', ack['s_id'], '\n')
              #  '\t', 'Destination:', ack['destination'])

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

def service_request(socket, **kwargs):
    request_msg = "sr_rs"
    request_ack = "rs_ack"
    request_nack = "rs_nack"

    # Send service release message to the hyperstrator
    socket.send_json({request_msg: {'s_id': kwargs['service_id']}})
    # Receive acknowledgment
    rep = socket.recv_json()

    # Check if there's an acknowledgement
    ack = rep.get(delete_ack, None)

    # If received an acknowledgement
    if ack is not None:
        print('- Request Service:')
        # Print information
        print('\t', 'Service ID:', ack['s_id'])
        # Exit gracefully
        exit(0)

    # Check if there's a not acknowledgement
    nack = rep.get(request_nack, None)

    # If received a not acknowledgement
    if nack is not None:
        print('- Failed to request information about service.')
        # Print reason
        print('\t', 'Reason: ', nack)
        # Opsie
        exit(0)

    # If neither worked
    if (ack is None) and (nack is None):
        print('- Failed to parse message:')
        print('\t', 'Message:', rep)

def service_update(socket, **kwargs):
    print('Not implemented.')
    exit(120)

def service_delete(socket, **kwargs):
    # Service Request - Delete Slice
    delete_msg = "sr_ds"
    delete_ack = "ds_ack"
    delete_nack = "ds_nack"

    # Send service release message to the hyperstrator
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
    # Establish connection to the hyperstrator
    socket = establish_connection()

    # Create new E2E service
    if 'create' in kwargs['subcommand']:
        service_create(socket, **kwargs)

    # Get information on E2E service
    elif 'request' in kwargs['subcommand']:
        service_request(socket, **kwargs)

    # Update configuration on E2E service
    elif 'update' in kwargs['subcommand']:
        service_update(socket, **kwargs)

    # Remove an E2E service
    elif 'delete' in kwargs['subcommand']:
        service_delete(socket, **kwargs)

    # Opsie
    else:
        print('Opsie, bad client. No subcommand found.')
        exit(100)
