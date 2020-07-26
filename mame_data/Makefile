DOCKER_IMAGE:=mame_data

build:
	docker build \
		--tag ${DOCKER_IMAGE} \
	.

run:
	docker run --rm -it ${DOCKER_IMAGE} /bin/sh
