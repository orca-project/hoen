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

from uuid import uuid4
import itertools

def cls():
    system('cls' if name=='nt' else 'clear')

class nsb(object):

	def __init__(self, datapath):
		(host, ovs_port) = datapath.address
		port = 4400
		self.dpid = datapath.id
		self._server_connect(host, port)
		
		self.q_number = itertools.count()
		self.default_qos = ""
		self.default_queue = {}
		self.speed = 104857600

	def _server_connect(self, host, port):
		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.REQ)
		self.socket.connect("tcp://" + host + ":" + str(port))
		self.socket.setsockopt(zmq.RCVTIMEO, 3000)
		self.socket.setsockopt(zmq.REQ_RELAXED, 1)
		self.socket.setsockopt(zmq.REQ_CORRELATE, 1)

	def reset_queues(self):
		t_id = str(uuid4())
		req = [{
				"t_id": t_id,
				"type": "reset_req",
				"default_queue": {
				"q_id": next(self.q_number),
				"min_rate": 0,
				"max_rate": self.speed,
				"priority": 100
				}
			}]
		(status, resp) = self._send_msg(req)
		if not status:
			return None

		for r in resp:
			if r.get('result_code') == 0 and r.get('t_id') == t_id:
				self.default_qos = r.get('default_qos')
				self.default_queue = r.get('default_queue')
				return r.get('default_queue').get('uuid')
		return None

	def create_queue(self, route):
		min_rate = None
		max_rate = None
		priority = None

		if 'min_rate' in route:
			min_rate = route['min_rate']
		if 'priority' in route:
			max_rate = route['max_rate']
		if 'min_rate' in route:
			priority = route['priority']

		if min_rate is None and max_rate is None and priority is None:
			return self.default_queue.get('q_id')

		t_id = str(uuid4())
		req = [{
			    "t_id": t_id,
			    "type": "create_req",
			    "qos": self.default_qos,
			    "queue": {
			      "q_id": next(self.q_number),
			      "min_rate": min_rate,
			      "max_rate": max_rate,
			      "priority": priority
			    }
			}]
		(status, resp) = self._send_msg(req)
		if not status:
			return None

		for r in resp:
			if r.get('result_code') == 0 and r.get('t_id') == t_id:
				return r.get('queue').get('q_id')
		return None

	def modify_default_queue(self, value):
		max_rate = self.default_queue.get('max_rate') - value
		if max_rate <= 0:
			# setting a max of 100Kb to ensure a minimum communication
			max_rate = 102400
		t_id = str(uuid4())
		req = [{
			    "t_id": t_id,
			    "type": "modify_req",
			    "queue": {
			      "uuid": self.default_queue.get('uuid'),
			      "max_rate": max_rate
			    }
			}]
		(status, resp) = self._send_msg(req)
		if status:
			self.default_queue['max_rate'] = self.default_queue.get('max_rate') - max_rate

	def _send_msg(self, req):
		self.socket.send_json(req)

		try:
			msg = self.socket.recv_json()
			return True, msg
		except zmq.Again:
			return False, "Connection timeout to " + str(self.dpid) + " switch"