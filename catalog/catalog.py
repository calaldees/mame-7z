import os
import datetime
import logging

import falcon


from scan import fast_scan


log = logging.getLogger(__name__)

FILE_RESCAN_SECONDS = 60


class CatalogData():
    def __init__(self, filehandle):
        self.mtime = {}


# Resources --------------------------------------------------------------------

class IndexResource():
    def on_get(self, request, response):
        response.media = {}
        response.status = falcon.HTTP_200


class NextFileResource():
    def __init__(self, path, catalog_data):
        self.path = path
        self.catalog_data = catalog_data
        self._files = []
        self._last_scan = None
    def _rescan_files(self):
        self._last_scan = datetime.datetime.now()
        self._files = [
            f
            for f in fast_scan(self.path)
            if (
                f.exists and
                f.stats.st_mtime != self.catalog_data.mtime.get(
                    os.path.join(f.folder, f.file_no_ext),
                    0,
                )
            )
        ]
    @property
    def files(self):
        if (
            not self._files
            and
            (
                self._last_scan == None
                or
                self._last_scan < datetime.datetime.now() - datetime.timedelta(seconds=FILE_RESCAN_SECONDS)
            )
        ):
            self._rescan_files()
        return self._files
    def on_get(self, request, response):
        files = self.files
        response.media = {
            'file': files.pop().relative if files else None,
            'remaining': len(files),
        }
        response.status = falcon.HTTP_200



# Setup App -------------------------------------------------------------------

def create_wsgi_app(path, catalog_data_filename, **kwargs):
    assert os.path.isfile(catalog_data_filename)
    with open(catalog_data_filename, 'rt') as filehandle:
        catalog_data = CatalogData(filehandle)

    app = falcon.API()
    app.add_route(r'/', IndexResource())
    app.add_route(r'/next_file', NextFileResource(path, catalog_data))

    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('path', action='store', default='/Users/allancallaghan/Applications/mame/roms/', help='')
    parser.add_argument('catalog_data_filename', action='store', default='./catalog.txt', help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=9002, type=int, help='')

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