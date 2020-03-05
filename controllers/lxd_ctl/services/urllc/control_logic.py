#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event

import time
import signal

references = [100, 100, 100, 100, 100]
#calibrate = True
calibrate = False
forward_speed = 40
backward_speed = 80
turning_angle = 40

max_off_track_count = 10

delay = 0.0005


class control(Thread):
    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # Connect to the server
        self.server_bind(**kwargs)

    def server_bind(self, **kwargs):
        # Default HS Server host
        host = kwargs.get('host', '0.0.0.0')
        # Default HS Server port
        port = kwargs.get('port', 9000)

        # Create a ZMQ context
        self.context = zmq.Context()
        # Specify the type of ZMQ socket
        self.socket = self.context.socket(zmq.REP)
        # Bind ZMQ socket to host:port
        self.socket.bind("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        #  self.socket.setsockopt(zmq.RCVTIMEO, 500)
        #  self.socket.setsockopt(zmq.SNDTIMEO, 500)
        #  self.socket.setsockopt(zmq.LINGER, 0)

    def run(self):
        print('- Started Car Control Logic')

        turning_angle = 0
        off_track_count = 0

        a_step = 3
        b_step = 10
        c_step = 30
        d_step = 43

        # Run while thread is active
        while not self.shutdown_flag.is_set():

            #  print('then here')
            try:
                message = self.socket.recv_json()
            # If nothing was received during the timeout
            except zmq.Again:
                continue

            else:

                measurement = message.get("measurement", None)
                print(measurement)

                # Angle calculate
                if measurement == "00100":
                    step = 0
                elif measurement in ["01100", "00110"]:
                    step = a_step
                elif measurement in ["01000", "00010"]:
                    step = b_step
                elif measurement in ["11000", "00011"]:
                    step = c_step
                elif measurement in ["10000", "00001"]:
                    step = d_step

                # Direction calculate
                if measurement == "00100":
                    off_track_count = 0
                    turning_angle = 90
                # turn right
                elif measurement in ["01100", "01000", "11000", "10000"]:
                    off_track_count = 0
                    turning_angle = int(90 - step)
                # turn left
                elif measurement in ["00110", "00010", "00011", "00001"]:
                    off_track_count = 0
                    turning_angle = int(90 + step)
                elif measurement == "00000":
                    off_track_count += 1
                    if off_track_count > max_off_track_count:
                        self.socket.send_json(
                            {'angle': 0, 'direction': 'back'})
                        continue

                else:
                    off_track_count = 0

                self.socket.send_json({'angle': turning_angle})
                #  time.sleep(delay)


        message = self.socket.recv_json()
        self.socket.send_json({'angle': 0, "direction": 'stop'})
        # Leaving the loop
        #  self.socket.send_json({'angle': 90, 'direction': 'stop'})


def straight_run():
    while True:
        bw.speed = 70
        bw.forward()
        fw.turn_straight()


def setup():
    if calibrate:
        cali()


def cali():
    references = [0, 0, 0, 0, 0]
    print(
        "cali for module:\n  first put all sensors on white, then put all sensors on black"
    )
    mount = 100
    fw.turn(70)
    print("\n cali white")
    time.sleep(4)
    fw.turn(90)
    white_references = lf.get_average(mount)
    fw.turn(95)
    time.sleep(0.5)
    fw.turn(85)
    time.sleep(0.5)
    fw.turn(90)
    time.sleep(1)

    fw.turn(110)
    print("\n cali black")
    time.sleep(4)
    fw.turn(90)
    black_references = lf.get_average(mount)
    fw.turn(95)
    time.sleep(0.5)
    fw.turn(85)
    time.sleep(0.5)
    fw.turn(90)
    time.sleep(1)

    for i in range(0, 5):
        references[i] = (white_references[i] + black_references[i]) / 2
    lf.references = references
    print("Middle references =", references)
    time.sleep(1)


if __name__ == '__main__':
    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the Remote Unit Server
        control_thread = control(host='0.0.0.0', port=9000)
        control_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Hyperstrator
        control_thread.shutdown_flag.set()
        control_thread.join()
        print('Exiting')
