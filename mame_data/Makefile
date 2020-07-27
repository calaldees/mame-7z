DOCKER_IMAGE:=mame_data

build:
	docker build \
		--tag ${DOCKER_IMAGE} \
	.

shell:
	docker run --rm -it \
		--publish 9001:9001 \
		${DOCKER_IMAGE} \
		/bin/sh
run:
	docker run --rm -it \
		--publish 9001:9001 \
		${DOCKER_IMAGE}
