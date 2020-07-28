import os.path
import json
import re
import logging
from functools import reduce
from collections import defaultdict
from types import MappingProxyType # https://stackoverflow.com/questions/41795116/difference-between-mappingproxytype-and-pep-416-frozendict

import falcon

from parse_xml import Rom


log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------

class RomData():
    """
    Romdata for 364682 in python3 memory takes 185Mb RAM
    """
    def __init__(self, filehandle):
        sha1 = {}
        archive = defaultdict(set)
        log.info('Loading rom data ...')
        for count, rom in enumerate(filter(None, map(Rom.parse, filehandle))):
            sha1[rom.sha1] = rom
            archive[rom.archive_name].add(rom)
            if count % 10000 == 0:
                print('.', end='', flush=True)
        print()
        self.sha1 = MappingProxyType(sha1)
        self.archive = MappingProxyType(archive)
        log.info(f'Loaded dataset for {count} roms')


# Request Handler --------------------------------------------------------------

class IndexResource():
    def on_get(self, request, response):
        response.media = {}
        response.status = falcon.HTTP_200

class SHA1InfoResource():
    def __init__(self, rom_data):
        self.rom_data = rom_data
    def on_get(self, request, response, sha1):
        rom = self.rom_data.sha1.get(sha1)
        if not rom:
            response.status = falcon.HTTP_404
            return
        response.media = {'rom': rom._asdict()}
        response.status = falcon.HTTP_200

class ArchiveResource():
    def __init__(self, rom_data):
        self.rom_data = rom_data
    def on_get(self, request, response):
        archive_name = request.path.strip('/archive/')  # HACK! The prefix route needs to be removed .. damnit ...
        archive_roms = self.rom_data.archive.get(archive_name)
        if not archive_roms:
            response.status = falcon.HTTP_404
            return
        response.media = {
            archive_name: {
                rom.sha1: rom.file_name
                for rom in archive_roms
            }
        }
        response.status = falcon.HTTP_200

class SetsResource():
    def __init__(self, rom_data):
        self.rom_data = rom_data
    def on_get(self, request, response):
        """
        curl \
            -D- \
            -H "Content-Type: application/json" \
            -X GET \
            --data '["3c912300775d1ad730dc35757e279c274c0acaad", "bd50a6bb8fa9bac121b076e21ea048a83a240a48"]' \
            "http://localhost:9001/sets"

        {"complete": {}, "incomplete": {"airlbios": ["bd50a6bb8fa9bac121b076e21ea048a83a240a48"], "3do": ["3c912300775d1ad730dc35757e279c274c0acaad"]}, "unknown": []}
        """
        response.media = {'complete': {}, 'incomplete': {}}
        roms_sha1 = set(request.media)
        roms = filter(None, map(lambda sha1: self.rom_data.sha1.get(sha1), request.media))
        archive_names = set(rom.archive_name for rom in roms)
        for archive_name in archive_names:
            archive_roms = self.rom_data.archive.get(archive_name)
            archive_sha1s = set(rom.sha1 for rom in archive_roms)
            if archive_sha1s < roms_sha1:
                response.media['complete'][archive_name] = tuple(archive_sha1s)
            elif archive_sha1s_incomplete := archive_sha1s & roms_sha1:
                response.media['incomplete'][archive_name] = tuple(archive_sha1s_incomplete)
            roms_sha1 -= archive_sha1s
        response.media['unknown'] = tuple(roms_sha1)
        response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(rom_data_filename, **kwargs):
    assert os.path.isfile(rom_data_filename)
    with open(rom_data_filename, 'rt') as filehandle:
        rom_data = RomData(filehandle)

    app = falcon.API()
    app.add_route(r'/', IndexResource())
    app.add_route(r'/sha1/{sha1}', SHA1InfoResource(rom_data))
    app.add_sink(ArchiveResource(rom_data).on_get, prefix=r'/archive/')
    app.add_route(r'/sets', SetsResource(rom_data))
    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('rom_data_filename', action='store', default='./roms.txt', help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=9001, type=int, help='')

    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    kwargs = vars(parser.parse_args())
    return kwargs


def init_sigterm_handler():
    """
    Docker Terminate
    https://itnext.io/containers-terminating-with-grace-d19e0ce34290
    #old - https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
    """
    import signal
    def handle_sigterm(*args):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, handle_sigterm)


# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    init_sigterm_handler()
    kwargs = get_args()

    logging.basicConfig(level=kwargs['log_level'])

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        log.info('start')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass