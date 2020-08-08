
help:
	# help

build:
	# build

test:
	pytest --doctest-modules -p no:cacheprovider

run:
	# run

romdata:
	python3 -m api_romdata.api api_romdata/roms.txt
catalog:
	python3 -m api_catalog.catalog /Users/allancallaghan/Applications/mame/roms/ api_catalog/catalog.txt
worker_catalog:
	python3 -m worker_catalog.worker_catalog /Users/allancallaghan/Applications/mame/roms/ http://localhost:9002