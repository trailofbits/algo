#!/usr/bin/env bash

# command line credentials should still work:
ansible-playbook tests/validate-aws-credentials.yml \
	-e aws_access_key=example_key \
	-e aws_secret_key=example_secret

# command line credentials should override config files:
ansible-playbook tests/validate-aws-credentials.yml \
	-e aws_access_key=example_key \
	-e aws_secret_key=example_secret

# In this case the config file is bad but the command line should win:
AWS_SHARED_CREDENTIALS_FILE="$PWD/tests/.aws/credentials2" \
	ansible-playbook tests/validate-aws-credentials.yml \
	-e aws_access_key=example_key \
	-e aws_secret_key=example_secret

# should read from the config file in tests/.aws:
HOME="$PWD/tests" \
	ansible-playbook tests/validate-aws-credentials.yml

AWS_SHARED_CREDENTIALS_FILE="$PWD/tests/.aws/credentials2" AWS_PROFILE=profile1 \
	ansible-playbook tests/validate-aws-credentials.yml
