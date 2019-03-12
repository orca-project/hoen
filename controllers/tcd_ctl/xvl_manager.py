import zmq
from json import dumps, loads


class xvl_client(object):
    def __init__(self, **kwargs):
        # Extract parameters from keyword arguments
        self.host = kwargs.get("host", "127.0.0.1")
        self.port = kwargs.get("port", 5000)
        self.rat_id = kwargs.get("rat_id", 0)
        self.debug = kwargs.get("debug", False)

        self.tx_port = 0
        self.rx_port = 0

    def _factory(self, message):
        # Create a ZMQ context
        context = zmq.Context()
        #  Specify the type of ZMQ socket
        socket = context.socket(zmq.REQ)

        if self.debug:
            print("Connecting to XVL server...")

        # Connect ZMQ socket to host:port
        socket.connect("tcp://" + self.host + ":" + str(self.port))

        if self.debug:
            print("Sending:\t" + str(message))

        socket.send_json(message)

        response = socket.recv_json()

        if self.debug:
            print(response)

        return response

    def check_connection(self):
        message = {"xvl_syn": ""}
        return self._factory(message)

    def query_resources(self):
        message = {"xvl_que": ""}
        return self._factory(message)

    def request_rx_resources(self, centre_freq, bandwidth):
        if not centre_freq or not bandwidth:
            raise Exception("Missing RX information!")

        message = {
            "xvl_rrx": {
                "id": self.rat_id,
                "centre_freq": centre_freq,
                "bandwidth": bandwidth,
                "ip": '127.0.0.1',
                "padding": 0
            }
        }

        root = self._factory(message)

        success = root['xvl_rep'].get('status', False)
        if success:
            return root['xvl_rep'].get('udp_port', 0)

        return 0

    def request_tx_resources(self, centre_freq, bandwidth):
        if not centre_freq or not bandwidth:
            raise Exception("Missing TX information!")

        message = {
            "xvl_rtx": {
                "id": self.rat_id,
                "centre_freq": centre_freq,
                "bandwidth": bandwidth,
                "ip": '127.0.0.1',
                "padding": 0
            }
        }

        root = self._factory(message)

        success = root['xvl_rep'].get('status', False)
        if success:
            return root['xvl_rep'].get('udp_port', 0)

        return 0

    def free_resources(self):
        message = {"xvl_fre": {"id": str(self.rat_id)}}
        return self._factory(message)
