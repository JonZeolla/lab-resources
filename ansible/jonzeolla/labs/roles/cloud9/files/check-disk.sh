#!/usr/bin/env bash

# Check that the primary disk is at least the size requested.

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
