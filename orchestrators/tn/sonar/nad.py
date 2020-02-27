#!/usr/bin/env python3

# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event

# Import SONAr modules
from sonar.log import get_log
from services.ndb import ndb

from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS

import logging

logger = get_log('sonar-nad')

class nad(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.app = Flask(__name__)
        CORS(self.app)
        self.api = Api(self.app)
        self.api.add_resource(PathAPI, '/orca/sonar/paths')
        self.api.add_resource(InformationAPI, '/orca/sonar/info')
        self.log = logging.getLogger('werkzeug')
        self.log.disabled = True
        self.app.logger.disabled = True

        self.shutdown_flag = Event()

    def run(self):
        print('- Started SONAr - Network Administration Dashboard')
        # Run while thread is active
        self.app.run(host='0.0.0.0', port='8080')

class PathAPI(Resource):
    def get(self):
        catalog = ndb()
        routes = catalog.get_routes()
        return {'routes': routes }

class InformationAPI(Resource):
    def get(self):
        catalog = ndb()
        topology = catalog.get_topology()
        capacity = catalog.get_capacity()
        routes = catalog.get_routes()
        networks = catalog.get_networks()
        usage = catalog.get_usage()
        flows = catalog.get_flows()
        local_agents = catalog.get_local_agents()
        configured_agents = catalog.get_configured_agents()
        path_latency = catalog.get_path_latencies()
        virtual_ifaces = catalog.get_virtual_ifaces()
        return {
            "topology": topology,
            "capacity": capacity,
            "routes": routes,
            "networks": networks,
            "usage": usage,
            "flows": flows,
            "local_agents": local_agents,
            "configured_agents": configured_agents,
            "path_latency": path_latency,
            "virtual_ifaces": virtual_ifaces
        }