#!/bin/bash


# Default parameters
lan="192.168.13.1"
gw="134.226.55.211"
ap="/root/openwifi/hostapd-openwifi.conf"
ftp=false


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
    # If fetching latest version through FTP
    if [ $ftp == true ]; then
        rm $submodule.ko
        sync
        wget ftp://$gw/driver/$submodule/$submodule.ko
        sync
    fi
    # Remo the existing module and install the new version
    rmmod $submodule
    insmod /root/openwifi/$submodule.ko

    # Check whether it worked
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

  # Path to devices
  dev_path="/sys/bus/iio/devices/iio:device"
  # Device index
  dev_index=-1
  # Iterate over possible devices
  for index in 0 1 2 3 4
  do
    # If the file exists
    if test -f $dev_path$index"/in_voltage_rf_bandwidth"; then
      # Get the index and break out of the loop
      dev_index=$index
      break
    fi
  done

  # Exit clause
  if [ $dev_index -lt "0" ]; then
    echo "Could not find in_voltage_rf_bandwidth!"
    echo "Check whether the ad9361 driver is loaded!"
    exit 100
  fi

  # Update the dev_path
  dev_path=$dev_path$dev_index

  # Container to hold parameters
  declare -A CONFIG

  CONFIG[in_voltage_rf_bandwidth]="17500000"
  CONFIG[out_voltage_rf_bandwidth]="37500000"

  CONFIG[in_voltage_sampling_frequency]="40000000"
  CONFIG[out_voltage_sampling_frequency]="40000000"

  CONFIG[out_altvoltage0_RX_LO_frequency]="5240000000"
  CONFIG[out_altvoltage1_TX_LO_frequency]="5250000000"

  # Set device's configuration parameters
  for key in "${!CONFIG[@]}"
  do
    echo "Setting $key"
    echo "${CONFIG[$key]}" > $dev_path/$key
    cat $dev_path/$key
    sync
  done

  # Configure the RF-frontend FIR
  echo "Setting AD9361 FIR"
  cat /root/openwifi/openwifi_ad9361_fir.ftr > $dev_path"/filter_fir_config"

  # Unset and clear the container
  unset CONFIG
  declare -A CONFIG

  CONFIG[in_voltage_filter_fir_en]="1"
  CONFIG[out_voltage_filter_fir_en]="0"

  CONFIG[in_voltage0_gain_control_mode]="fast_attack"
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


# Handle loading kernel modules
kernelHandle () {
  modprobe mac80211

  # Start removing the sdr module
  rmmod sdr

  loadModules "xilinx_dma" "tx_intf" "ad9361_drv"

  echo "set RF frontend: ant0 rx, ant1 tx"
  rfInit

  loadModules "rx_intf" "openofdm_tx" "openofdm_rx" "xpu" "sdr"
}

modprobe mac80211

# Core functionality
main () {

  service network-manager stop
  echo "Stopped NM"
  kernelHandle
  echo "Configured interface"
  sleep 20
  ifconfig sdr0 $lan
  echo "Set sdr0's IP"
  ip route add default via $gw dev eth0
  echo "Set default route"
  service isc-dhcp-server restart
  echo "Restarted DHCP server"
  sleep 5
  hostapd -B $ap
  echo "Started AP"

}


# Parse CLI arguments
while getopts "l:g:a:r" arg; do
  case $arg in
    l) lan=${OPTARG};;
    g) gw=${OPTARG};;
    a) ap=${OPTARG};;
    r) fpt=true;;
    \?)	echo "Usage: $0 [-l lan_ip] [-g gw_ip] [-ap hostapd_conf] [-r]";exit;;
  esac
done

# Run main
main
