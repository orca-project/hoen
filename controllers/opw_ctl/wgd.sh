#!/bin/bash
set -x

checkModule () {
  MODULE="$1"
  if lsmod | grep "$MODULE" &> /dev/null ; then
    echo "$MODULE is loaded!"
    return 0
  else
    echo "$MODULE is not loaded!"
    return 1
  fi
}

loadModules () {
  submodules=("$@")
  for submodule in "${submodules[@]}"
  do
    rmmod $submodule
    insmod ~/openwifi/$submodule.ko

    echo check $submodule module is loaded or not
    checkModule $submodule
    if [ $? -eq 1 ]
    then
      return
    fi

    sleep 1
  done
}

kernelHandle () {
  modprobe mac80211

  loadModules "xilinx_dma" "tx_intf" "ad9361_drv"

  echo "set RF frontend: ant0 rx, ant1 tx"
  ~/openwifi/rf_init.sh

  loadModules "rx_intf" "openofdm_tx" "openofdm_rx" "xpu" "sdr"
}

service network-manager stop
echo "Stopped NM"
kernelHandle > ~/log/wgd.out 2> ~/log/wgd.err &
echo "Configured interface"
sleep 20
ifconfig sdr0 192.168.13.1
echo "Set sdr0's IP"
ip route add default via 134.226.55.211 dev eth0
echo "Set default route"
service isc-dhcp-server restart
echo "Restarted DHCP server"
nohup hostapd ~/openwifi/hostapd-openwifi.conf > ~/log/apt.out 2> ~/log/apt.err &
echo "Started AP"
sleep 5
