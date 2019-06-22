## docker-build: Build and tag a docker image
.PHONY: docker-build

IMAGE          := trailofbits/algo
TAG	  	       := latest
DOCKERFILE     := Dockerfile
CONFIGURATIONS := $(shell pwd)

docker-build:
	docker build \
	-t $(IMAGE):$(TAG) \
	-f $(DOCKERFILE) \
	.

## docker-deploy: Mount config directory and deploy Algo
.PHONY: docker-deploy

# Set DOCKER_BUILD flag for main algo script.
docker-deploy:
	docker run \
	--cap-drop=all \
	--rm \
	-it \
	-v $(CONFIGURATIONS):/data \
	$(IMAGE):$(TAG)

## docker-clean: Remove images and containers.
.PHONY: docker-clean

docker-clean:
	docker images \
	$(IMAGE) |\
	awk '{if (NR>1) print $$3}' |\
	xargs docker rmi

## docker-all: Build, Deploy, Rinse
.PHONY: docker-all

## docker-ci-local
.PHONY: docker-ci-local

DEPLOY_ARGS := 'provider=local server=10.0.8.100 ssh_user=ubuntu endpoint=10.0.8.100 apparmor_enabled=false ondemand_cellular=true ondemand_wifi=true ondemand_wifi_exclude=test local_dns=true ssh_tunneling=true windows=true store_cakey=true install_headers=false tests=true local_service_ip=172.16.0.1'

docker-ci-local:
	docker run \
	-it \
	-v $(shell pwd)/config.cfg:/algo/config.cfg \
	-v $(shell echo ${HOME})/.ssh:/root/.ssh \
	-v $(shell pwd)/configs:/algo/configs \
	-e "DEPLOY_ARGS=$(DEPLOY_ARGS)" \
	trailofbits/algo:latest /bin/sh -c "chown -R root: /root/.ssh && chmod -R 600 /root/.ssh && ansible-playbook main.yml -e ${DEPLOY_ARGS} --skip-tags apparmor"

## docker-ci-user-update
.PHONY: docker-ci-user-update

USER_ARGS := '{ 'server': '10.0.8.100', 'users': ['desktop', 'user1', 'user2'], 'local_service_ip': '172.16.0.1' }'

docker-ci-user-update:
	docker run \
	-it \
	-v $(shell pwd)/config.cfg:/algo/config.cfg \
	-v $(shell echo ${HOME})/.ssh:/root/.ssh \
	-v $(shell pwd)/configs:/algo/configs \
	-e "USER_ARGS=$(USER_ARGS)" \
	trailofbits/algo:latest /bin/sh -c "ansible-playbook users.yml -e ${USER_ARGS} -t update-users"

all: docker-build docker-deploy docker-clean
