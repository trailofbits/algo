#!/bin/bash
set -eux

apt-get update -y
apt-get install sudo -y

getent passwd algo || useradd -m -d /home/algo -s /bin/bash -G adm,netdev -p '!' algo

(umask 337 && echo "algo ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/10-algo-user)

cat <<EOF >/etc/ssh/sshd_config
{{ lookup('template', 'files/cloud-init/sshd_config') }}
EOF

test -d /home/algo/.ssh || (umask 077 && sudo -u algo mkdir -p /home/algo/.ssh/)
echo "{{ lookup('file', '{{ SSH_keys.public }}') }}" | (umask 177 && sudo -u algo tee /home/algo/.ssh/authorized_keys)

sudo apt-get remove -y --purge sshguard || true
systemctl restart sshd.service
