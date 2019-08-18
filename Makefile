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

# '--rm' flag removes the container when finished.
docker-deploy:
	docker run \
	--cap-drop=all \
	--rm \
	-it \
	-v $(CONFIGURATIONS):/data \
	$(IMAGE):$(TAG)

## docker-clean: Remove images and containers.
.PHONY: docker-prune

docker-prune:
	docker images \
	$(IMAGE) |\
	awk '{if (NR>1) print $$3}' |\
	xargs docker rmi

## docker-all: Build, Deploy, Prune
.PHONY: docker-all

docker-all: docker-build docker-deploy docker-prune
