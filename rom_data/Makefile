DOCKER_IMAGE:=mame_data
GIT_TAG:=mame0222


build:
	docker build \
		--tag ${DOCKER_IMAGE} \
		--build-arg ${GIT_TAG}
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
