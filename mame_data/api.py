import os.path
import json
import re
import logging

import falcon

from parse_xml import Rom


log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

class RomData():
    def __init__(self, filehandle):
        log.info('Loading rom data ...')
        for rom in filter(None, map(Rom.parse, filehandle)):
            pass


# Request Handler --------------------------------------------------------------

class SHA1InfoResource():
    def __init__(self):
        pass
    def on_get(self, request, response, sha1):
        response.media = {'status': 'ok', 'sha1': sha1}
        response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(rom_data_filename, **kwargs):
    with open(rom_data_filename, 'rt') as filehandle:
        rom_data = RomData(filehandle)

    app = falcon.API()
    app.add_route('/sha1/{sha1}', SHA1InfoResource())
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
    https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
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
