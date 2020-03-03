#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event
# Import the uuid4 function from the UUID module
from uuid import uuid4
# Import the system method from the OS module
from os import system, name
# Import the Pause method from the Signal module
from signal import pause

import time
import subprocess
import itertools

import platform

def cls():
    system('cls' if name == 'nt' else 'clear')

class local_agent_server(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)

        self.shutdown_flag = Event()
        self._server_connect(host, port)

        self.src = []
        self.dst = []
        self.management_iface = ""
        self.seq = itertools.count()

    def _server_connect(self, host, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://" + host + ":" + str(port))
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.socket.setsockopt(zmq.REQ_RELAXED, 1)
        self.socket.setsockopt(zmq.REQ_CORRELATE, 1)

    def _send_msg(self, req):
        self.socket.send_json(req)
        try:
            msg = self.socket.recv_json()
            return True, msg
        except zmq.Again:
            return False, "Connection timeout to SONAr server"

    def _send_config_msg(self, req):
        self.socket.send_json(req)
        while True:
            try:
                msg = self.socket.recv_json()
                return True, msg
            except zmq.Again:
                continue

    def run(self):
        print('- Started SONAr local agent')
        t_id = str(uuid4())
        req = {
                "t_id": t_id,
                "type": "config_req",
                "name": platform.node()
              }
        (status, resp) = self._send_config_msg(req)
        if resp.get('result_code') == 0 and resp.get('type') == 'config_resp':
            self.boot_service(resp)
            self.collect_metrics()
        else:
            print('- Error trying get config information', resp)
            self.socket.close()
            self.context.term()


    def collect_metrics(self):
        while True:
            t_id = str(uuid4())
            metrics = []
            for src in self.src:
                for dst in self.dst:
                    # add here other metrics
                    metrics.append(self.collect_latency(src, dst))
            req = {
                    "t_id": t_id,
                    "type": "report_req",
                    "metrics": metrics
                }
            (status, resp) = self._send_msg(req)
            print('status', status)
            print('resp', resp)
            time.sleep(1)

    def boot_service(self, operation):
        self.management_iface = operation.get('management_iface')

        del_command = 'for i in `ifconfig | grep ' + self.management_iface + ':' + 'sonar | cut -d":" -f2` ;do ifconfig ' + self.management_iface + ':$i down ;done'
        (dc, do) = self.run_system_command(del_command)
        if dc != 0:
            return False
        del self.src[:]
        del self.dst[:]

        for src in operation.get('src'):
            self.src.append(src)
            seq = next(self.seq)
            command = 'ifconfig ' + self.management_iface + ':sonar' + str(seq) + ' ' + str(src) + ' netmask 255.255.255.0'
            (c, o) = self.run_system_command(command)
            if c != 0:
                return False
                #return self.boot_resp(t_id, 2)

        for dst in operation.get('dst'):
            self.dst.append(dst)
        return True

    def run_system_command(self, command):
        print(command)
        resp =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        resp.wait()
        out = resp.stdout.read().decode().strip()
        code = resp.returncode
        return code, out

    def collect_latency(self, src, dst):
        command = 'ping -c 2 -I ' + src + ' ' + dst + ' | tail -1 | awk \'{ print $4 }\''
        (code, out) = self.run_system_command(command)
        if code == 0 and len(out) > 0:
            p = out.split('/')
            metric = {
                        "timestamp": time.time(),
                        "type": "latency",
                        "src": src,
                        "dst": dst,
                        "params": {
                          "min": p[0],
                          "avg": p[1],
                          "max": p[2],
                          "mdev": p[3]
                        }
                    }
        else:
            metric = {
                        "timestamp": time.time(),
                        "type": "latency",
                        "src": src,
                        "dst": dst,
                        "params": {
                          "min":-1,
                          "avg": -1,
                          "max": -1,
                          "mdev": -1
                        }
                    }
        return metric

if __name__ == "__main__":
    cls()

    try:
        sonar_host = '100.1.2.1'
        port = 5500
        local_agent_thread = local_agent_server(sonar_host, port)
        local_agent_thread.start()
        pause()

    except KeyboardInterrupt:
        local_agent_thread.shutdown_flag.set()
        local_agent_thread.join()
        print('Exiting')
