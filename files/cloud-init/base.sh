#!/bin/bash
set -euxo pipefail

readonly user='algo'

export DEBIAN_FRONTEND='noninteractive'

until which sudo; do
    apt-get update -qq
    apt-get install -qqf --install-suggests sudo
    sleep 3
done

getent passwd "${user}" \
    || useradd -m -d "/home/${user}" -s /bin/bash -G adm -p '!' "${user}"

(
    umask 0337 \
        && printf '%s\n' "${user} ALL=(ALL) NOPASSWD:ALL" \
        >"/etc/sudoers.d/10-algo-user"
)

printf "{{ lookup('template', 'files/cloud-init/sshd_config') }}\n" \
    >/etc/ssh/sshd_config

# This should be idempotent; correct permsission on .ssh dir if exists
install -o "${user}" -g "${user}" -m 0700 -d "/home/${user}/.ssh"

# umask does not reliably work with sudo
install -o "${user}" -g "${user}" -m 0600 \
    /dev/null "/home/${user}/.ssh/authorized_keys"

printf "{{ lookup('file', '{{ SSH_keys.public }}') }}\n" \
    >"/home/${user}/.ssh/authorized_keys"

until ! dpkg -l sshguard; do
    apt-get remove -qq --purge sshguard
    sleep 3
done || :

systemctl restart sshd.service
