#!/bin/bash

sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o wlp5s0  -j MASQUERADE
sudo ip route add 192.168.13.0/24 via 134.226.55.100 dev enp0s31f6
# sudo ip route add 192.168.20.0/24 via 134.226.55.100 dev enp0s31f6
