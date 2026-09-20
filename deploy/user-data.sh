#!/bin/bash
# EC2 first-boot script (Amazon Linux 2023). Installs Docker and the Compose
# plugin, then gets out of the way — scripts/deploy.sh does the actual app
# deploy over SSH afterwards, so re-deploys don't need to relaunch the instance.
set -euo pipefail

dnf update -y
dnf install -y docker

systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

mkdir -p /usr/local/lib/docker/cli-plugins
curl -sSL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

mkdir -p /home/ec2-user/chronolab
chown ec2-user:ec2-user /home/ec2-user/chronolab
