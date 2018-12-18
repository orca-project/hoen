# y2sc3

## Installation

This repository includes a list of required Python 3 modules, which can be installed with:
```console
$ pip3 install -r requirements.txt
```
I personally recommend using a virtual environment.

## Description

Currently, this repository includes:
1. A high level utility for requesting/removing E2E services, the *service_request.py*.
2. The Hyperstrator, which interfaces with Wired and Wireless orchestrators to deploy E2E services, the *hyperstrator.py*.
3. A stub Wired Network Orchestrator, which will SDN things in the future, the *sdn_orch.py*. It doesn't do anything at the moment.
4. A functional Wireless Network Orchestrator, the *sdr_orch.py*. It delegates Radio requests to IMEC and TCD according to the requested traffic type.
5. Stub SDR controllers for IMEC and TCD, the *imec_controller.py* and *tcd_controller.py*, respectively. 

## Running

You need to start the controllers, the Wired Network Orchestrator and the Hyperstrator to test the whole system. You can start them in any order, but all of them must be running for it to work.

For example, run the IMEC and TCD controllers (in different tabs, windows, or terminals):
```console
$ ./imec_controller.py
```
```console
$ ./tcd_controller.py
```
Then, run the Wireless Network Orchestrator:
```console
$ ./sdr_orch.py
```
Finally, the Hyperstrator:
```console
$ ./hyperstrator.py
```

Now, you can play with the *service_request.py*. Passing the flag *-t* indicates a high-throughput traffic, while the *-l* flag indicates low-latency traffic. They are mutually exclusive. 
Upon successful reservation, you will receive the service ID of your E2E communication service, a UUID. Moreover, you can pass the flag *-s* with a valid service ID to remove a given service.

It also possess a help flag (*-h*):

```console
$ ./service_request.py -h
usage: service_request.py [-h] (-l | -t | -s SERVICE_ID)

Manage E2E Services

optional arguments:
  -h, --help            show this help message and exit
  -l, --low-latency     Low-Latency Service
  -t, --high-throughput
                        High-Throughput Service
  -s SERVICE_ID, --service-id SERVICE_ID
```
## Controller

As stated above, there are two stub controllers, behaving as placeholders: *imec_controller.py* and *tcd_controller.py*. 
Currently, each stub controller possesses two methods that IMEC and TCD must implement/override in their respective controller: the *create_slice* and *remove_slice*. 
Both IMEC and TCD are free to implement, use, call, integrate, or whatever, in any way they please. Really, do whatever you want.
We just need you to react to the calls of these two methods and return the appropriate formatted messages, as exemplified in the source-code of the stub controllers.

Ideally, you won't need to modify anything apart from your respective controllers. Please enter in contact with me if you find any bugs/unexpected behaviour.

# Branches

There are 4 branches in thisrepository:
1. The *master* branch. Let's leave it as it is, failsafe and working.
2. The *imec*  branch. I kindly ask to IMEC to use this branch for the testing and development of their SDR part.
3. The *tcd*  branch. I kindly ask to TCD to use this branch for the testing and development of their SDR part.
4. The *dev*  branch. I will use this here for development, testing, and breaking changes. As well as incorporate the SDN part in the future.
