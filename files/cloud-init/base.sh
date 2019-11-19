#!/bin/bash
set -eux

apt-get update -y
apt-get install sudo -y

getent passwd algo || useradd -m -d /home/algo -s /bin/bash -G sudo -p '!' algo

cat <<EOF >/etc/sudoers.d/10-algo-user
algo ALL=(ALL) NOPASSWD:ALL
EOF

cat <<EOF >/etc/ssh/sshd_config
{{ lookup('template', 'files/cloud-init/sshd_config') }}
EOF

test -d /home/algo/.ssh || sudo -u algo mkdir -p /home/algo/.ssh/
echo "{{ lookup('file', '{{ SSH_keys.public }}') }}" | sudo -u algo tee /home/algo/.ssh/authorized_keys

sudo apt-get remove -y --purge sshguard || true
systemctl restart sshd.service
