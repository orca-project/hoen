#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the sleep function from the time module
from time import sleep
# Import the System and Name methods from the OS module
from os import system, name

import signal

def cls():
    system('cls' if name=='nt' else 'clear')

class nsb(object):

	def __init__(self, datapath):
		(host, ovs_port) = datapath.address
		port = 4400
		self.dpid = datapath.id
		self._server_connect(host, port)
		self.q_number = -1

	def _server_connect(self, host, port):
		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.REQ)
		self.socket.connect("tcp://" + host + ":" + str(port))
		self.socket.setsockopt(zmq.RCVTIMEO, 3000)
		self.socket.setsockopt(zmq.REQ_RELAXED, 1)
		self.socket.setsockopt(zmq.REQ_CORRELATE, 1)

	def reset_queues(self):
		 self.q_number = self.q_number + 1
		req = [{
				"t_id": "123",
				"type": "reset_req",
				"default_queue": {
				"q_id": self.q_number,
				"min_rate": 0,
				"max_rate": 10485760,
				"priority": 100
				}
			}]
		(status, resp) = self._send_msg(req)
		print(resp)

	def _send_msg(self, req):
		self.socket.send_json(req)

		try:
			msg = self.socket.recv_json()
			return True, msg
		except zmq.Again:
			return False, "Connection timeout to " + str(self.dpid) + " switch"