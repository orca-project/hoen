#!/bin/bash

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
    insmod /root/openwifi/$submodule.ko

    echo check $submodule module is loaded or not
    checkModule $submodule
    if [ $? -eq 1 ]
    then
      return
    fi

    sleep 1
    echo "Loaded "$submodule
  done
}

rfInit () {
			
  # Path to device
  dev_path="/sys/bus/iio/devices/iio:device2"

  # Container to hold parameters
  declare -A CONFIG

  #CONFIG[in_voltage_rf_bandwidth]="37500000"
  CONFIG[in_voltage_rf_bandwidth]="17500000"

  #CONFIG[out_voltage_rf_bandwidth]="40000000"
  #CONFIG[out_voltage_rf_bandwidth]="20000000"
  CONFIG[out_voltage_rf_bandwidth]="37500000"

  #CONFIG[in_voltage_sampling_frequency]="20000000"
  CONFIG[in_voltage_sampling_frequency]="40000000"

  #CONFIG[out_voltage_sampling_frequency]="20000000"
  CONFIG[out_voltage_sampling_frequency]="40000000"

  #CONFIG[out_altvoltage0_RX_LO_frequency]="2320000000"
  #CONFIG[out_altvoltage0_RX_LO_frequency]="2427000000"
  CONFIG[out_altvoltage0_RX_LO_frequency]="5240000000"

  #CONFIG[out_altvoltage1_TX_LO_frequency]="2320000000"
  #CONFIG[out_altvoltage1_TX_LO_frequency]="2447000000"
  CONFIG[out_altvoltage1_TX_LO_frequency]="5250000000"

  #CONFIG[in_voltage0_gain_control_mode]="manual"
  CONFIG[in_voltage0_gain_control_mode]="fast_attack"

  #CONFIG[in_voltage1_gain_control_mode]="manual"
  CONFIG[in_voltage1_gain_control_mode]="fast_attack"

  CONFIG[in_voltage0_hardwaregain]="70"
  CONFIG[in_voltage1_hardwaregain]="70"

  CONFIG[out_voltage0_hardwaregain]="-89"
  CONFIG[out_voltage1_hardwaregain]="0"

  # Set device's configuration parameters
  for key in "${!CONFIG[@]}"
  do
    echo "Setting $key"
    echo "${CONFIG[$key]}" > $dev_path/$key
    cat $dev_path/$key
    sync
  done
}

kernelHandle () {
  modprobe mac80211

  loadModules "xilinx_dma" "tx_intf" "ad9361_drv"

  echo "set RF frontend: ant0 rx, ant1 tx"
  rfInit

  loadModules "rx_intf" "openofdm_tx" "openofdm_rx" "xpu" "sdr"
}

service network-manager stop
echo "Stopped NM"
kernelHandle > /root/log/kml.out &
echo "Configured interface"
sleep 20
ifconfig sdr0 192.168.13.1
echo "Set sdr0's IP"
ip route add default via 134.226.55.211 dev eth0
echo "Set default route"
service isc-dhcp-server restart
echo "Restarted DHCP server"
nohup hostapd openwifi/hostapd-openwifi.conf > /root/log/apd.out &
echo "Started AP"
sleep 5
