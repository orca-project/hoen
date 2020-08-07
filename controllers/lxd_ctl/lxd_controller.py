#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller, cls
# Import OS
import os
# Import signal
import signal
# Import the net_if_address from the ps_util module
from psutil import net_if_addrs
# Import the Client class from the pylxd module
from pylxd import Client

from time import time

#  from threading import Thread

# Supress pylxd warnings
os.environ["PYLXD_WARNINGS"] = "none"
grab_ethernet = True

class lxd_controller(base_controller):

    def post_init(self, **kwargs):
        # Instantiate the LXD client
        self.lxd_client = Client()

        # List of external ethernet ports
        self.interface_list = {x: {"available": True} for x in \
                net_if_addrs().keys() if x.startswith('enp') and x != 'enp4s0'}

        self._log("Found", len(self.interface_list),
                  "Ethernet ports:", list(self.interface_list.keys()))

    def prepare_distro_image(self, image_name="hoen-3.0"):
        # Image server locations
        #  image_server = "https://images.linuxcontainers.org"
        image_server = "https://cloud-images.ubuntu.com/releases/"

        # Check if we have the right type of distributions
        if image_name.split("-")[0].lower() not  in ['ubuntu','hoen']:
            raise ValueError('Only supports Ubuntu distributions:', image_name)

        # Check if the image is stored in the local repository
        if image_name not in \
                [x.aliases[0]['name'] for x in \
                    self.lxd_client.images.all() if x.aliases]:
            # Output status message
            self._log("Downloading ", image_name)

            # Try to get the new image
            image = self.lxd_client.images.create_from_simplestreams(
                image_server, image_name.split("-")[1])

            # Check whether we have an alias for it already
            if 'name' not in image.aliases:
                # If not, add the alias
                image.add_alias(name=image_name, description="")

        # Log event and return possible new name
        self._log("Base image ready:", image_name)

        return image_name


    def create_slice(self, **kwargs):
       # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))
        s_ser = kwargs.get('service', "best-effort")
        # TODO: Ideally the CN orchestrator would specify the resources
        i_cpu = str(kwargs.get('i_cpu', 1))
        f_ram = str(int(kwargs.get('f_ram', 1.0)))

        if grab_ethernet:
            # Try to get an available interface
            index = 0
            available_interface = ""
            # Iterate over the interface list
            for index, interface in enumerate(self.interface_list):
                if self.interface_list[interface]['available']:
                    # Use the first available interface and break the loop
                    available_interface = interface
                    self.interface_list[interface]['available'] = False
                    break

            # If there are no interfaces available
            if not available_interface:
                # Log event and return message
                self._log('Not enough resources!')
                return False, 'Not enough resources!'

        try:

            # Get the latest hoen immage
            hoen_images = sorted([x.aliases[0]['name'] for x in
                                  self.lxd_client.images.all() if x.aliases and
                                  x.aliases[0]["name"].startswith("hoen")])

            # If there aren't any HOEN images available
            if not hoen_images:
                raise ValueError("Missing HOEN images.")

            #  Prepare image of the last HOEN image
            s_distro = self.prepare_distro_image(hoen_images[-1])

        except Exception as e:
            #  Log event and return
            self._log("Could not prepare base image:", str(e))
            return False, str(e)


        # Default container profile configuration
        profile = {'name':  "id-" + s_id,
                   'config': {
                     'security.nesting': 'true',
                     'limits.cpu': i_cpu,
                     'limits.memory': f_ram + "GB"},
                   'source': {'type': 'image', 'alias': s_distro},
                   'profiles': ['hoen'],
                   'devices': {
                       "repo": {"type": "disk",
                                "source": os.getcwd() + "/services/", #TODO from type of service
                                "path": "/root/services/"}
                   }}


        # If attaching an physical ethernet port to it
        if grab_ethernet:
            # Add new entry to the profile configuration
            profile['devices'].update({"oth0": {
                "type": "nic",
                "nictype": "physical",
                "parent": available_interface,
                "name": "oth0"}
            })


        # Try to create a new container
        try:
            # Create a new container with the specified configuration
            container = self.lxd_client.containers.create(profile, wait=True)
            self._log("Created container")

            # Start the container
            container.start(wait=True)
            self._log("Started container")

            # If attaching an physical ethernet port to it
            if grab_ethernet:
                # Set the interface's IPenp0s31f6
                interface_ip = "30.0.{0}.1/24".format(int(available_interface[3]))
                container.execute(
                        ["ip", "addr", "add", interface_ip, "dev", "oth0"])

                self._log("Configured IP:", interface_ip)

                # Install routes to allow different network communication
                container.execute(
                    ["ip", "route", "add", "default", "dev", "oth0"]
                )

                # Set route to radio
                container.execute(
                    ['ip','route','add','10.0.0.0/24','via', '10.0.0.1', 'dev',
                     'oth0']
                )

                self._log("Configured networking")

                if False:
                    # Start docker service
                    self.start_service(container, s_ser)

        # In case of issues
        except Exception as e:
            # If attaching an physical ethernet port to it
            if grab_ethernet:
                # Release resources
                self.interface_list[interface]['available'] = True

            # Log event and return
            self._log(str(e))
            return False, str(e)

        # In case it worked out fine
        else:
            # Append it to the service list
            self.s_ids[s_id].update({"container": container,
                                     "service": s_ser})

            # If attaching an physical ethernet port to it
            if grab_ethernet:
                self.s_ids[s_id].update({"interface": available_interface})
            # Log event and return

            self._log("Created container!")

            return True, {
                's_id': s_id,
                "source": interface_ip if grab_ethernet else "127.0.0.1"}

    def start_service(self, container, s_ser):
        self._log("Starting Docker Service")
        t = time()

        # Ensure docker daemon is already started
        container.execute(["systemctl", "start", "docker"])
        # Run required service
        container.execute(["docker", "start", s_ser])
        # Running iperf3 for any service just for testing
        container.execute(["docker", "start", "test"])

        self._log("Docker services started in", round(time() - t, 3), "seconds")


    def request_slice(self, **kwargs):
      # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Container to hold the requested information
        msg = {}
        # Iterate over all containers
        for container in self.lxd_client.containers.all():
            # If going for a specific S_ID but it does not match
            if (s_id and ("id-" + s_id != container.name)) or \
                    not container.name.startswith("id"):
                continue

            # Log event and return
            self._log("Found container:", container.name.split('-',1)[-1])

            # Append this information to the output dictionary
            msg[container.name.split('-',1)[-1]] = {
                #  'distro': container.config["image.os"]+ "-" + \
                    #  container.config['image.version'],
                'memory': {"limit": container.config.get('limits.memory', ""),
                    "usage": container.state().memory['usage']},
                'cpu': {"limit":  container.config.get('limits.cpu', ""),
                    "usage": container.state().cpu['usage']}
            }

            if container.name.split('-',1)[-1] in self.s_ids:
                # Add it to the message
                msg[container.name.split('-',1)[-1]].update(
                    {"service": \
                         self.s_ids[container.name.split('-',1)[-1]]["service"]
                     })

            # If there is an external Ethernet interface
            if grab_ethernet and container.state().network is not None:

                # Add it to the message
                msg[container.name.split('-',1)[-1]].update(
                    {"network":
                     {"oth0": container.state().network["oth0"]['counters']}
                })

        # If there's an S_ID but the result was empty
        return (False, "Container missing.") \
            if (s_id and not msg) else (True, msg)

    def delete_slice(self, **kwargs):
      # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

        # Default value
        container = None
        # Iterate over all container and return the matching one
        for ctn in self.lxd_client.containers.all():
            if "id-" + s_id == ctn.name:
                # Get the right container
                container = ctn
                break

        # Check whether it exists
        if container is None:
            # In case the records are outdated
            return False, "Container missing."

        # Stop the container if necessary
        if container.status.lower() != "stopped":
            # Stop the container
            container.stop(wait=True)
            # Log event
            self._log("Stopped container:", s_id)

        try:
            # Delete the container
            container.delete()
        except Exception as e:
            # Log event and return
            self._log(str(e))
            return False, str(e)
        # In case it worked out fine
        else:
            # If set to have its own physical NIC
            if grab_ethernet:
                # Release resources
                self.interface_list[ \
                    self.s_ids[s_id]["interface"]]["available"] = True

            # Log event and return
            self._log("Deleted container!")
            return True, {"s_id": s_id}

if __name__ == "__main__":
    # Clear screen
    cls()
    # Handle keyboard interrupt (SIGINT)
    try:
        # Instantiate the LXD Controller
        lxd_controller_thread = lxd_controller(
            name='LXD',
            req_header='lxd_req',  # Don't modify
            rep_header='lxd_rep',  # Don't modify
            create_msg='lcc_crs',
            request_msg='lcc_rrs',
            update_msg='lcc_urs',
            delete_msg='lcc_drs',
            host='0.0.0.0',
            port=3300)

        # Start the LXD Controller Server
        lxd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the LXD Controller Server
        lxd_controller_thread.safe_shutdown()
