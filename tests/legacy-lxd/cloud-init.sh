#!/bin/bash
# Use environment variables or defaults
REPO=${REPOSITORY:-trailofbits/algo}
BRANCH_NAME=${BRANCH:-master}

cat << EOF
#cloud-config
# Disable automatic package updates to avoid APT lock conflicts
package_update: false
package_upgrade: false
runcmd:
  - |
    #!/bin/bash
    set -ex
    
    # Wait for any running apt processes to finish
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
      echo "Waiting for apt locks to be released..."
      sleep 5
    done
    
    # Fix DNS resolution
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    echo "127.0.0.1 algo" >> /etc/hosts
    
    # Update packages manually after ensuring no locks
    apt-get update || true
    apt-get upgrade -y || true
    
    export METHOD=local
    export ONDEMAND_CELLULAR=true
    export ONDEMAND_WIFI=true
    export ONDEMAND_WIFI_EXCLUDE=test1,test2
    export STORE_PKI=true
    export DNS_ADBLOCKING=true
    export SSH_TUNNELING=true
    export ENDPOINT=10.0.8.100
    export USERS=desktop,user1,user2
    export EXTRA_VARS='install_headers=false tests=true local_service_ip=172.16.0.1'
    export ANSIBLE_EXTRA_ARGS=''
    export REPO_SLUG=${REPO}
    export REPO_BRANCH=${BRANCH_NAME}
    
    curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH_NAME}/install.sh | sudo -E bash -x
EOF
