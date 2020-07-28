DOCKER_IMAGE:=compression_tools

build:
	docker build \
		--tag ${DOCKER_IMAGE} \
	.

shell:
	docker run --rm -it \
		${DOCKER_IMAGE} \
		/bin/sh
run:
	docker run --rm -it \
		${DOCKER_IMAGE}
