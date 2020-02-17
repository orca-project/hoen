#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hack to load parent module
from sys import path
path.append('..')

# Import the Template Controller
from base_controller.base_controller import base_controller
# Import OS
import os
# Import signal
import signal
# Import the Time method from the time module
from time import time
# Import the net_if_address from the ps_util module
from psutil import net_if_addrs
# Import the Client class from the pylxd module
from pylxd import Client

# Supress pylxd warnings
os.environ["PYLXD_WARNINGS"] = "none"


class lxd_controller(base_controller):

    def post_init(self, **kwargs):
        # Instantiate the LXD client
        self.lxd_client = Client()


        self.interface_list = {x: {"available": True} for x in \
                net_if_addrs().keys() if x.startswith('enp')}

    def prepare_distro_image(self, image_name="ubuntu-19.04-plain"):
        # Keep track of time spent here
        st = time()
        # Image server locations
        #  image_server = "https://images.linuxcontainers.org"
        image_server = "https://cloud-images.ubuntu.com/releases/"

        # Split the name for later use
        name_split = image_name.split('-')
        # If missing the type of image, use vanilla
        if len(name_split) == 2:
            # And update the name & split
            image_name += "-plain"
            name_split += ["plain"]

        # Check if we have the right type of distributions
        if name_split[0].lower() != 'ubuntu':
            raise ValueError('Only supports Ubuntu distributions:', image_name)

        # Check if the image is stored in the local repository
        if image_name not in \
                [x.aliases[0]['name'] for x in self.lxd_client.images.all() if x.aliases]:
            self._log("Downloading ", image_name)

            # If using a custom image #TODO
            if  name_split[2].lower() != "plain":
                raise ValueError('Not dealing with custom images at the moment:', image_name)

            # Get vanilla image
            else:
                # Try to get the new image
                image = self.lxd_client.images.create_from_simplestreams(
                    image_server, name_split[1])

            # Check whether we have an alias for it already
            if 'name' not in image.aliases:
                # If not, add the alias
                image.add_alias(name=image_name, description="")

        # Log event and return possible new name
        self._log("Base image ready!", (time()-st)*1000, "ms")
        return image_name


    def create_slice(self, **kwargs):
         # Keep track of time spent here
        st = time()
       # Extract parameters from keyword arguments
        s_id = str(kwargs.get('s_id', None))
        s_distro = kwargs.get('s_distro', "ubuntu-19.04-plain")
        # TODO: Ideally the CN orchestrator would specify the resources
        i_cpu = kwargs.get('i_cpu', 1)
        f_ram = kwargs.get('s_ram', 1.0)

       # Check for validity of the slice ID
        if s_id in self.slice_list:
            self._log('Creation did not work!', 'Took',
                      (time() - st)*1000, 'ms')
            return False, 'Slice ID already exists'

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
            self._log('Not enough resources!', 'Took',
                      (time() - st)*1000, 'ms')
            return False, 'Not enough resources!'

        #  Check if container already exist
        #  if self.get_slice(name) is not None:
            #  self.log('Container', name, 'already exists!')
        #  If not, lets create it
        #  else:

        try:
            #  Prepare image of the chosen distribution
            s_distro = self.prepare_distro_image(s_distro)

        except Exception as e:
            #  Log event and return
            self._log("Could not prepare base image:", str(e))
            return False, str(e)

        # Try to create a new container
        try:
            # Create a new container with the specified configuration
            container = self.lxd_client.containers.create(
                {'name':  "id-" + s_id,
                 'source': {'type': 'image', 'alias': s_distro},
                 'devices': {"oth0": {"type": "nic",
                                      "nictype": "physical",
                                      "parent": available_interface,
                                      "name": "oth0"}}
                 },
                 wait=True)

            # Start the container
            container.start(wait=True)

            # Set the interface's IP
            interface_ip = "10.0.{0}.1/24".format(index)
            container.execute(
                    ["ip", "addr", "add", interface_ip, "dev", "oth0"])
            # And log event
            self._log("Configured IP:", interface_ip)

        # In case of issues
        except Exception as e:
            # Release resources
            self.interface_list[interface]['available'] = True
            # Log event and return
            self._log(str(e))
            return False, str(e)

        # In case it worked out fine
        else:
            # Append it to the service list
            self.slice_list[s_id] = {
                    "container": container,
                    "interface": available_interface}
            # Log event and return
            self._log("Created container!", "Took:", (time()-st)*1000, "ms")
            return True, {'s_id': s_id, "source": interface_ip}

    def request_slice(self, **kwargs):
         # Keep track of time spent here
        st = time()
      # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

       # Check for validity of the slice ID
        if s_id not in self.slice_list:
            self._log('Request did not work!', 'Took', (time() - st)*1000, 'ms')
            return True, {"s_id": s_id,
                          "info": 'There is no slice with this ID'}

        # Iterate over all container and return the matching one
        for container in self.lxd_client.containers.all():
            if "id-" + s_id == container.name:
                # Get info about the OS. #TODO CPU & RAM, maybe?
                s_distro = container.config["image.os"]+ "-" + \
                    container.config['image.version']
                # Log event and return
                self._log("Found container!", "Took:", (time()-st)*1000, "ms")
                return True, {"s_id": s_id,
                        "info": {"s_distro": s_distro,
                                 "interface": self.slice_list[s_id]['interface']
                                 }}

        # In case the records are outdated
        return False, "Container missing."

    def delete_slice(self, **kwargs):
        # Keep track of time spent here
        st = time()
      # Extract parameters from keyword arguments
        s_id = kwargs.get('s_id', None)

       # Check for validity of the slice ID
        if s_id not in self.slice_list:
            # Log event and return
            self._log('Delete did not work!', 'Took',
                      (time() - st)*1000, 'ms')
            return False, 'There is no slice with this ID'

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
            # Release resources
            self.interface_list[self.slice_list[s_id]["interface"]]["available"] = True
            # Remove container from list
            self.slice_list.pop(s_id)
            # Log event and return
            self._log("Deleted container!", "Took:", (time()-st)*1000, "ms")
            return True, {"s_id": s_id}


if __name__ == "__main__":

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
            host='127.0.0.1',
            port=3300)

        # Start the LXD Controller Server
        lxd_controller_thread.start()
        # Pause the main thread
        signal.pause()

    except KeyboardInterrupt:
        # Terminate the LXD Controller Server
        lxd_controller_thread.safe_shutdown()
