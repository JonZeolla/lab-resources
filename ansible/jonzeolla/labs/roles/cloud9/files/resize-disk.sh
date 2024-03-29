#!/usr/bin/env bash
# This is a lightly modified version of https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html#move-environment-resize

touchfile="/tmp/.resize-disk"
if [[ -r "${touchfile}" ]]; then
  echo "Skipping the resize-disk.sh because it last completed at $(stat -c %y "${touchfile}")"
  exit
fi

function sudo_if_needed() {
  if [[ "$(whoami)" == "root" ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

# Check for AWS creds
aws sts get-caller-identity || exit 1

# Specify the desired volume size in GiB as a command line argument. If not specified, default to 20 GiB.
SIZE=${1:-40}

# Get the ID of the environment host Amazon EC2 instance.
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
INSTANCEID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/instance-id 2> /dev/null)
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/placement/region 2> /dev/null)

# Get the ID of the Amazon EBS volume associated with the instance.
VOLUMEID=$(aws ec2 describe-instances \
  --instance-id "$INSTANCEID" \
  --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
  --output text \
  --region "$REGION")

# Resize the EBS volume.
aws ec2 modify-volume --volume-id "$VOLUMEID" --size "$SIZE"

# Wait for the resize to finish.
# shellcheck disable=SC2140
while [ \
  "$(aws ec2 describe-volumes-modifications \
    --volume-id "$VOLUMEID" \
    --filters Name=modification-state,Values="optimizing","completed" \
    --query "length(VolumesModifications)"\
    --output text)" != "1" ]; do
  sleep 1
done

# Check if we're on an NVMe filesystem
if [[ -e "/dev/xvda" && $(readlink -f /dev/xvda) = "/dev/xvda" ]]; then
  DISK="/dev/xvda"
  PARTITION="${DISK}1"
else
  DISK="/dev/nvme0n1"
  PARTITION="${DISK}p1"
fi

STR=$(cat /etc/os-release)
SUBAL2="VERSION_ID=\"2\""
SUBAL2023="VERSION_ID=\"2023\""

# Rewrite the partition table so that the partition takes up all the space that it can.
sudo_if_needed growpart "${DISK}" 1

# Check if we're on AL2 or AL2023 (indirectly checking for XFS) and extend the filesystem appropriately
if [[ "$STR" == *"$SUBAL2"* || "$STR" == *"$SUBAL2023"* ]]; then
  sudo_if_needed xfs_growfs -d /
else
  sudo_if_needed resize2fs "${PARTITION}"
fi

touch "${touchfile}"
