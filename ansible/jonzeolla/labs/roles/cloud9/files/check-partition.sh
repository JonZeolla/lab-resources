#!/usr/bin/env bash

# Check that the primary disk is at least the size requested, and that the primary partition has also been resized

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <desired size in GB>"
  exit 1
fi

desired_size_in_gb="$1"
primary_disk="$(df / | tail -1 | awk '{print $1}')"

# Purposefully using 1000**3 instead of 1024**3 to check in GB, not GiB.
desired_size="$((desired_size_in_gb * 1000**3))"
actual_size="$(lsblk -b -n -d -o SIZE "$primary_disk")"

if [[ "${actual_size}" -lt "${desired_size}" ]]; then
  echo "Disk ${primary_disk} is too small: ${actual_size}B < ${desired_size}B"
  exit 1
fi

partition_name="$(lsblk -o NAME,SIZE,MOUNTPOINT | awk '$NF == "/" {print $1}' | sed 's/^[^a-zA-Z0-9]*//')"
partition_size="$(lsblk -o NAME,SIZE,MOUNTPOINT | awk '$NF == "/" {print $2}')"

if [[ "${partition_size}" != "${desired_size_in_gb}G" ]]; then
  echo "Partition ${partition_name} is too small: ${partition_size} < ${desired_size_in_gb}G"
  exit 1
fi
