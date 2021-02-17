## docker-build: Build and tag a docker image
.PHONY: docker-build

IMAGE 		:= trailofbits/algo
TAG			:= latest
DOCKERFILE	:= Dockerfile
PWD			:= $$(pwd)

docker-build:
	docker build \
	-t $(IMAGE):$(TAG) \
	-f $(DOCKERFILE) \
	.

## docker-deploy: Mount config directory and deploy Algo
.PHONY: docker-deploy

# '--rm' flag removes the container when finished.
docker-deploy:
	docker run \
	--cap-drop=all \
	--rm \
	-it \
	-v $(PWD):/data \
	$(IMAGE):$(TAG)

# update the users on existing VPN
.PHONY: docker-update

docker-update:
	docker run \
	--cap-drop=all \
	--rm \
	-it \
	-e "ALGO_ARGS=update-users" \
	-v $(PWD):/data \
	$(IMAGE):$(TAG)

## docker-prune: Remove images and containers.
.PHONY: docker-prune

docker-prune:
	docker images \
	$(IMAGE) |\
	awk '{if (NR>1) print $$3}' |\
	xargs docker rmi

## docker-all: Build, Deploy, Prune
.PHONY: docker-all

docker-all: docker-build docker-deploy docker-prune
