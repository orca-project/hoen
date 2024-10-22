#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the ArgParse modeule
import argparse
# Import JSON
from json import loads, dumps

RECV_DELAY = 60*1000

# Make printing easier. TODO: Implement real logging
def log(*args, head=False):
    print("-" if head else '\t' ,*args)

def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Manage E2E Services')

    parser.add_argument(
        '-s', '--server',
        type=str,
        default='127.0.0.1',
        required=False,
        help='Hyperstrator server IP')
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=1100,
        required=False,
        help='Hyperstrator server port')


    # Create subparsers
    subparsers = parser.add_subparsers(help='Sub-command Help',
                                       dest='subcommand')
    # Require subcommands
    subparsers.required = True

    # Parent parser for parameters shared among sub-parsers
    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument(
        '-j', '--json_output',
        required=False,
        action='store_true',
        help='Strip text and return a JSON string')
    parent_parser.add_argument(
        '-J', '--json_input',
        required=False,
        type=loads,
        help='Input as JSON string')


    # Create parser for getting information about the network
    parser_info = subparsers.add_parser(
        'info',
        parents=[parent_parser],
        help='Get information about the network infrastructure')

    # Add CLI arguments
    parser_info.add_argument(
        '-n', '--network',
        metavar='S_NS',
        type=str,
        choices=["ran", "tn", "cn"],
        nargs='+',
        required=False,
        default=["ran", "tn", "cn"],
        help='Network Segments')


    # Create parser for the creation of slices
    parser_create = subparsers.add_parser(
        'create',
        parents=[parent_parser],
        help='Create a new E2E Network Slice',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Add CLI arguments
    parser_create.add_argument(
        '-s', '--service',
        metavar='SERVICE',
        type=str,
        choices=["best-effort", "embb", "urllc"],
        default='best-effort',
        #  required=True, # I wonder whether this arguments must be required
        help='Type of Service')

    parser_create.add_argument(
        '-t', '--throughput',
        type=float,
        help='Required throughput [Mbps]')
    parser_create.add_argument(
        '-l', '--latency',
        type=float,
        help='Required latency [ms]')

    parser_create.add_argument(
        '-a', '--application',
        metavar='APPLICATION',
        type=str,
        choices=["video", "robot", "debug"],
        default='debug',
        #  required=True, # I wonder whether this arguments must be required
        help='Type of Application')

    # Create parser for the getting information about the slices
    parser_request = subparsers.add_parser(
        'request',
        parents=[parent_parser],
        help='Request information about  E2E Network Slice')

    # Add CLI arguments
    parser_request.add_argument(
        '-i', '--s_id',
        metavar='S_ID',
        type=str,
        required=False,
        help='Request information about this service')


    # TODO Built parsers, but methods remain unimplemented
    if False:
        parser_update = subparsers.add_parsers(
            'update',
            parents=[parent_parser],
            help='Reconfigure an E2E Network Slice'
        )

        parser_updated.add_argument(
            '-i', '--s_id',
            metavar='S_ID',
            type=str,
            required=False,
            help='Update requirements for this service'
        )
        parser_update.add_argument(
            '-t', '--throughput',
            type=float,
            default=1.0,
            help='Required throughput [Mbps]')
        parser_update.add_argument(
            '-l', '--latency',
            type=float,
            default=10.0,
            help='Required latency [ms]')

    # Create parser for the removal of slices
    parser_delete = subparsers.add_parser(
        'delete',
        parents=[parent_parser],
        help='Remove an existing E2E Network Slice')

    # Add CLI arguments
    parser_delete.add_argument(
        '-i', '--s_id',
        metavar='S_ID',
        type=str,
        required=False,
        help='Remove service based on the S_ID')


    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    return arg_dict


def establish_connection(**kwargs):
    # Default hyperstrator server IP
    server = kwargs.get('server', '127.0.0.1')
    # Default hyperstrator server port
    port = kwargs.get('port', 1100)

    # Create a ZMQ context
    context = zmq.Context()
    #  Specify the type of ZMQ socket
    socket = context.socket(zmq.REQ)

    socket.setsockopt(zmq.RCVTIMEO, RECV_DELAY)
    socket.setsockopt(zmq.LINGER, 0)

    try:
        # Connect ZMQ socket to server:port
         socket.connect("tcp://" + server + ":" + str(port))
    except zmq.error.Again:
        log('Could not reach the Hyperstrator server at:',
            server + ":" + str(port))

    return socket


def network_info(socket, **kwargs):
    info_msg = "ns_ni"
    info_ack = "ni_ack"
    info_nack = "ni_nack"

    # Try to get the network segment
    s_ns = list(set(kwargs.get("network", "")))

    # Send message to the hyperstrator
    socket.send_json({info_msg: {'s_ns': s_ns}})

    try:
        # Receive acknowledgment
         rep = socket.recv_json()

    except zmq.error.Again:
        log('Could not reach the Hyperstrator server at:',
            kwargs['server'] + ":" + str(kwargs['port']), head=True)

    else:
        # Check if there's an acknowledgement
        ack = rep.get(info_ack, None)

        # If received an acknowledgement
        if ack is not None:
            # If returning a human-readable string
            if not kwargs['json_output']:
                # Print information
                log('Network Information:', head=True)
                # For every returned slice
                for entry in ack:
                    log('Network Segment:', entry)
                    log('Info:', ack[entry])

            # If returning a raw JSON
            else:
                print(dumps(ack))

            # Exit gracefully
            exit(0)

        # Check if there's a not acknowledgement
        nack = rep.get(info_nack, None)

        # If received a not acknowledgement
        if nack is not None:
            log('Failed to request information about network segment.',
                head=True)
            # Print reason
            log('Reason: ', nack, head=True)
            # Opsie
            exit(0)

        # If neither worked
        if (ack is None) and (nack is None):
            log('Failed to parse message:', head=True)
            log('Message:', rep)


def service_create(socket, **kwargs):
    # Service Request - Create Slice
    create_msg = 'sr_cs'
    create_ack = 'cs_ack'
    create_nack = 'cs_nack'

    # Send service request message to the hyperstrator
    socket.send_json({
        create_msg: {'service': kwargs['service'],
                     'application': kwargs['application'],
                     'requirements': {'throughput': kwargs['throughput'],
                                      'latency': kwargs['latency']}
                     }})

    try:
        # Receive acknowledgment
         rep = socket.recv_json()

    except zmq.error.Again:
        log('Could not reach the Hyperstrator server at:',
            kwargs['server'] + ":" + str(kwargs['port']), head=True)

    else:
        # Check if there's an acknowledgment
        ack = rep.get(create_ack, None)

        # If received an acknowledgement
        if ack is not None:
            # If returning a human-readable string
            if not kwargs['json_output']:
                log('Created Service:', head=True)
                # Print information
                log('Service ID:', ack['s_id'])
                    #  '\t', 'Destination:', ack['destination'])

            # If returning a raw JSON
            else:
                print(dumps(ack))

            # Exit gracefully
            exit(0)

        # Check if there's a not acknowledgement
        nack = rep.get(create_nack, None)

        # If received a not acknowledgement
        if nack is not None:
            log('Failed to create service.', head=True)
            # Print reason
            log('Reason: ', nack)
            # Opsie
            exit(0)

        # If neither worked
        if (ack is None) and (nack is None):
            log('Failed to parse message:', head=True)
            log('Message:', rep)

def service_request(socket, **kwargs):
    request_msg = "sr_rs"
    request_ack = "rs_ack"
    request_nack = "rs_nack"

    # Try to get the service ID
    s_id = kwargs.get("s_id", "")

    # Send service release message to the hyperstrator
    socket.send_json({request_msg: {'s_id': s_id}})

    try:
        # Receive acknowledgment
         rep = socket.recv_json()

    except zmq.error.Again:
        log('Could not reach the Hyperstrator server at:',
            kwargs['server'] + ":" + str(kwargs['port']), head=True)

    else:
        # Check if there's an acknowledgement
        ack = rep.get(request_ack, None)

        # If received an acknowledgement
        if ack is not None:
            # If returning a human-readable string
            if not kwargs['json_output']:
                # Print information
                log('Request Service:', head=True)
                # For every returned slice
                for entry in ack:
                    log('Service ID:', entry)
                    log('Info:', ack[entry])

            # If returning a raw JSON
            else:
                print(dumps(ack))

            # Exit gracefully
            exit(0)

        # Check if there's a not acknowledgement
        nack = rep.get(request_nack, None)

        # If received a not acknowledgement
        if nack is not None:
            log('Failed to request information about service.', head=True)
            # Print reason
            log('Reason: ', nack, head=True)
            # Opsie
            exit(0)

        # If neither worked
        if (ack is None) and (nack is None):
            log('Failed to parse message:', head=True)
            log('Message:', rep)

def service_update(socket, **kwargs):
    log('Not implemented.')
    exit(120)

def service_delete(socket, **kwargs):
    # Service Request - Delete Slice
    delete_msg = "sr_ds"
    delete_ack = "ds_ack"
    delete_nack = "ds_nack"

    if not kwargs['s_id']:
        log("Missing service ID", head=True)
        exit(121)

    # Send service release message to the hyperstrator
    socket.send_json({delete_msg: {'s_id': kwargs['s_id']}})

    try:
        # Receive acknowledgment
         rep = socket.recv_json()

    except zmq.error.Again:
        log('Could not reach the Hyperstrator server at:',
            kwargs['server'] + ":" + str(kwargs['port']), head=True)

    else:
        # Check if there's an acknowledgement
        ack = rep.get(delete_ack, None)

        # If received an acknowledgement
        if ack is not None:
            # If returning a human-readable string
            if not kwargs['json_output']:
                log('Removed Service:', head=True)
                # Print information
                log('Service ID:', ack['s_id'])
            # If returning a raw JSON
            else:
                print(dumps(ack))

            # Exit gracefully
            exit(0)

        # Check if there's a not acknowledgement
        nack = rep.get(delete_nack, None)

        # If received a not acknowledgement
        if nack is not None:
            log('Failed to remove service.', head=True)
            # Print reason
            log('Reason: ', nack)
            # Opsie
            exit(0)

        # If neither worked
        if (ack is None) and (nack is None):
            log('Failed to parse message:', head=True)
            log('Message:', rep)


if __name__ == "__main__":
    # Parse CLI arguments
    kwargs = parse_cli_args()
    # Establish connection to the hyperstrator
    socket = establish_connection()

    # Override input with JSON input
    if 'json_input' in kwargs and kwargs['json_input']:
        for key in kwargs['json_input']:
            kwargs[key] = kwargs['json_input'][key]

    # Retrieve information about the E2E network
    if 'info' in kwargs['subcommand']:
        network_info(socket, **kwargs)

    # Create new E2E service
    elif 'create' in kwargs['subcommand']:
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

    # Unexpected
    else:
        log('Opsie, bad client. No subcommand found.', head=True)
        exit(100)
