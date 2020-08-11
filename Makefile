DOCKER_IMAGE:=romcheck

help:
	# help

build:
	#docker build --tag ${DOCKER_IMAGE} --build-arg MAME_GIT_TAG=mame0222 .
	docker-compose build

test:
	pytest --doctest-modules -p no:cacheprovider

run:
	docker build --tag ${DOCKER_IMAGE}-temp --target requirements .
	docker run --rm -it ${DOCKER_IMAGE}-temp /bin/sh

romdata:
	python3 -m api_romdata.api api_romdata/roms.txt
catalog:
	python3 -m api_catalog.catalog /Users/allancallaghan/Applications/mame/roms/ api_catalog/catalog.txt
worker_catalog:
	python3 -m worker_catalog.worker_catalog /Users/allancallaghan/Applications/mame/roms/ http://localhost:9002