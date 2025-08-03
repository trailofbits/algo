#!/bin/bash
# Use environment variables or defaults
REPO=${REPOSITORY:-trailofbits/algo}
BRANCH_NAME=${BRANCH:-master}

cat << EOF
#cloud-config
package_update: true
package_upgrade: true
runcmd:
  - |
    #!/bin/bash
    set -ex
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
