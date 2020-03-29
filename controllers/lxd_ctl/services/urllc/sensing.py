#!/usr/bin/env python3

# Import the ZMQ module
import zmq
# Import the Thread and Lock objects from the threading module
from threading import Thread, Lock, Event

from picar import front_wheels
from picar import back_wheels
from picar import ADC

import picar
import signal
import smbus
import math
import time

# Umport the ArgParse module
import argparse

def parse_cli_args():
    # Instantiate ArgumentParser object
    parser = argparse.ArgumentParser(description='Car Configuration')
    # Add CLI arguments
    parser.add_argument( '-s', '--speed', type=int, default=35, help='Car Speed')
    parser.add_argument( '-p', '--port', type=int, default=9000, help='Service Port')
    parser.add_argument( '-n', '--host', type=str, default='127.0.0.1', help='Service Host')
    parser.add_argument( '-r', '--reference', type=int, default=300, help='IR Reference Value')

    # Parse CLI arguments
    arg_dict = vars(parser.parse_args())

    return arg_dict


class sensing(Thread):
    def __init__(self, **kwargs):
        # Initialise the parent class
        Thread.__init__(self)
        # Flat to exit gracefully
        self.shutdown_flag = Event()
        # Start the HS server
        self.server_connect(**kwargs)

        # Create SMBus instance
        self.bus = smbus.SMBus(1)
        self.address = 0x11

        # Initial direction
        self.direction = ''

        self.references = 5 * [kwargs.get('reference', 600)]
        self.referneces = [600, 600, 600, 600, 800]
        
        self.speed = kwargs.get('speed', 35)
        self.turn = 44

        picar.setup()
        # Initialise the wheel objects
        self.front_wheels = front_wheels.Front_Wheels(db='config')
        self.back_wheels = back_wheels.Back_Wheels(db='config')

        print('configured wheels')

    def server_connect(self, **kwargs):
        # Default Server host
        host = kwargs.get('host', '127.0.0.1')
        # Default Server port
        port = kwargs.get('port', 9000)
        # Create a ZMQ context

        self.context = zmq.Context()
        #  Specity the type of ZMQ socket
        self.socket = self.context.socket(zmq.REQ)
        # Connect ZMQ socket to host:port
        self.socket.connect("tcp://" + host + ":" + str(port))
        # Timeout reception every 500 milliseconds
        #  self.socket.setsockopt(zmq.RCVTIMEO, 500)
        #  self.socket.setsockopt(zmq.SNDTIMEO, 500)
        #  self.socket.setsockopt(zmq.REQ_RELAXED, 1)
        #  self.socket.setsockopt(zmq.LINGER, 0)

    # Read RAW values from I2C
    def read_raw(self):
        # Read the 5-sensor array
        for i in range(0, 5):
            # Try to query the I2C bus
            try:
                raw_result = self.bus.read_i2c_block_data(self.address, 0, 10)
                # Set flag
                Connection_OK = True
                # Exit loop
                break
            # In case of issues
            except:
                # Set flag
                Connection_OK = False

        # If the connection was OK
        if Connection_OK:
            # Return the raw result list
            return raw_result
        # Otherwise
        else:
            # Return error flag and output error message
            print("Error accessing %2X" % self.address)
            return False

    def read_analog(self, trys=5):
        for _ in range(trys):
            raw_result = self.read_raw()
            if raw_result:
                analog_result = [0, 0, 0, 0, 0]
                for i in range(0, 5):
                    high_byte = raw_result[i*2] << 8
                    low_byte = raw_result[i*2+1]
                    analog_result[i] = high_byte + low_byte
                    if analog_result[i] > 1024:
                        continue
                return analog_result
        else:
            raise IOError("Line follower read error. Please check the wiring.")

    def read_digital(self):
        lt = self.read_analog()
        digital_list = []
        for i in range(0, 5):
            if lt[i] >= self.references[i]:
                digital_list.append(0)
            elif lt[i] < self.references[i]:
                digital_list.append(1)
            else:
                digital_list.append(-1)
        return digital_list

    def run(self):
        print('- Started PiCAR')
        # Start the wheel controls
        self.front_wheels.ready()
        self.back_wheels.ready()

        # Set max turning angle
        self.front_wheels.turning_max = self.turn
        # Set the speed
        self.back_wheels.speed = self.speed

        print('\t Speed:', self.speed)
        print('\t Turn:', self.turn)

        self.back_wheels.backward()

        # Run while thread is active
        while not self.shutdown_flag.is_set():

        # Move frontwards (the directions are reversed for some reason)

            try:
                # Inform the user about the removal success
                self.socket.send_json({
                  'measurement':
                 "".join(str(x) for x in self.read_digital())
                })
            except:
                raise

            else:

                #  cmd = self.socket.recv_json()
                try:
                    # wait for command
                    cmd = self.socket.recv_json()

                except zmq.Again:
                    # Try again
                    self.back_wheels.stop()
                    continue

                else:
                    # Extract angle direction from input command
                    turning_angle = cmd.get('angle', 0)
                    new_direction = cmd.get('direction', 'front')

                    # Turn wheels accordingly
                    self.front_wheels.turn(turning_angle)

                    if new_direction == 'stop':
                        break

                    # Check whether to change directions
                    if new_direction != self.direction:
                        # Update direction
                        self.direction = new_direction
                        # Change directions
                        self.back_wheels.backward() if \
                            new_direction == 'front' else \
                            self.back_wheels.forward()

        #  time.sleep(0.001)

        print('Exiting')
        self.front_wheels.turn(90)
        self.back_wheels.stop()

    def get_average(self, mount):
        if not isinstance(mount, int):
            raise ValueError("Mount must be interger")
        average = [0, 0, 0, 0, 0]
        lt_list = [[], [], [], [], []]
        for times in range(0, mount):
            lt = self.read_analog()
            for lt_id in range(0, 5):
                lt_list[lt_id].append(lt[lt_id])
        for lt_id in range(0, 5):
            average[lt_id] = int(math.fsum(lt_list[lt_id]) / mount)
        return average

    def wait_tile_center(self):
        while True:
            lt_status = self.read_digital()
            if lt_status[2] == 1:
                break


if __name__ == '__main__':

    cli_args = parse_cli_args()

    # Handle keyboard interrupt (SIGINT)
    try:
        # Start the robot thread
        robot_thread = sensing(**cli_args)

        robot_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the Hyperstrator
        robot_thread.shutdown_flag.set()
        robot_thread.front_wheels.turn(90)
        robot_thread.back_wheels.stop()

        robot_thread.join()
