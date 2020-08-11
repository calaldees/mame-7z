import os
import datetime
import logging
import re
from functools import reduce
from pathlib import Path

import falcon

from _common.scan import fast_scan
from _common.roms import RomData, Rom

log = logging.getLogger(__name__)

FILE_RESCAN_SECONDS = 60


class CatalogData(RomData):
    def __init__(self, catalog_data_filename, catalog_mtime_filename):
        super().__init__(catalog_data_filename, readonly=False)
        self.catalog_data_filename = catalog_data_filename
        self.catalog_mtime_filename = catalog_mtime_filename
        self._open_mtime()
    def _open_mtime(self):
        self.mtime = {}
        if not os.path.isfile(self.catalog_mtime_filename):
            return
        with open(self.catalog_mtime_filename, 'r') as filehandle:
            for line in filehandle:
                archive_name, mtime = (i.strip() for i in line.split(':'))
                self.mtime[archive_name] = mtime
    def save(self):
        """
        Save state of in memory object back to disk
        """
        log.info('Saving catalog_data in memory to disk')
        with open(self.catalog_data_filename, 'w') as filehandle:
            for count, rom in enumerate(
                rom
                for archive_roms in self.archive.values()
                for rom in archive_roms
            ):
                filehandle.write(f'{rom}\n')
                if count % 10000 == 0:
                    print('.', end='', flush=True)
        with open(self.catalog_mtime_filename, 'w') as filehandle:
            for archive_name, mtime in self.mtime.items():
                    filehandle.write(f'{archive_name}:{mtime}\n')
    def replace_roms(self, roms):
        """
        TODO: doctest
        """
        def _group_roms_by_archive_name(acc, rom):
            acc.setdefault(rom.archive_name, set()).add(rom)
            return acc
        for archive_name, roms in reduce(_group_roms_by_archive_name, roms, {}).items():
            _old_roms = self.archive.get(archive_name, ())
            self.archive[archive_name] = roms
            for _old_rom in _old_roms:
                _roms_with_sha1 = self.sha1.get(_old_rom.sha1)
                _roms_with_sha1.discard({r for r in _roms_with_sha1 if r.archive_name == archive_name})



# Resources --------------------------------------------------------------------

class IndexResource():
    def __init__(self, catalog_data):
        self.catalog_data = catalog_data
    def on_get(self, request, response):
        response.media = {
            'sha1': len(self.catalog_data.sha1.keys()),
            'archive': len(self.catalog_data.archive.keys()),
        }
        response.status = falcon.HTTP_200


class ArchiveResource():
    def __init__(self, catalog_data):
        self.catalog_data = catalog_data
    def _sink(self, request, response):
        """
        """
        archive = Path(re.sub(r'^/archive/', '', request.path))  # # HACK! The prefix route needs to be removed .. damnit ...
        archive_name = os.path.join(archive.parent.name, archive.stem)  # TODO: duplicated in catalog worker - maybe move to `Roms`?
        if not archive_name:
            return self.on_index(request, response)  # This is really bad - my implementation of sink is horrible
        return getattr(self, f'on_{request.method.lower()}')(request, response, archive_name)
    def on_index(self, request, response):
        response.media = tuple(self.catalog_data.archive.keys())
        response.status = falcon.HTTP_200
    def on_get(self, request, response, archive_name):
        """
        TODO: I don't like the return - multiple archives?
        """
        catalog_roms = self.catalog_data.archive.get(archive_name)
        if not catalog_roms:
            response.media = {}
            response.status = falcon.HTTP_404
            return
        response.media = {
            #archive_name: {
                rom.sha1: rom.file_name
                for rom in catalog_roms
            #}
        }
    def on_post(self, request, response, archive_name):
        self.catalog_data.replace_roms(Rom(**rom_dict) for rom_dict in request.media['roms'])
        self.catalog_data.mtime[archive_name] = request.media['mtime']
        response.status = falcon.HTTP_200


class NextUntrackedFileResource():
    def __init__(self, path, catalog_data):
        self.path = path
        self.catalog_data = catalog_data
        self._files = []
        self._last_scan = None
    def _rescan_files(self):
        self._last_scan = datetime.datetime.now()
        def _filter_files(f):
            return (
                f.exists
                and
                str(f.stats.st_mtime) != self.catalog_data.mtime.get(
                    os.path.join(f.folder, f.file_no_ext)
                )
            )
        self._files = list(filter(_filter_files, fast_scan(self.path)))
    @property
    def files(self):
        if (
            not self._files
            and
            (
                self._last_scan == None
                or
                self._last_scan < (datetime.datetime.now() - datetime.timedelta(seconds=FILE_RESCAN_SECONDS))
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

def create_wsgi_app(rom_path, catalog_data_filename, catalog_mtime_filename, **kwargs):
    catalog_data = CatalogData(catalog_data_filename, catalog_mtime_filename)
    init_sigterm_handler(catalog_data.save)

    app = falcon.API()
    app.add_route(r'/', IndexResource(catalog_data))
    app.add_route(r'/next_file', NextUntrackedFileResource(rom_path, catalog_data))
    app.add_sink(ArchiveResource(catalog_data)._sink, prefix=r'/archive/')

    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('--rom_path', action='store', required=True, help='')
    parser.add_argument('--catalog_data_filename', action='store', required=True, default='./catalog.txt', help='')
    parser.add_argument('--catalog_mtime_filename', action='store', required=True, default='./mtimes.txt', help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=9002, type=int, help='')

    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    kwargs = vars(parser.parse_args())
    return kwargs


def init_sigterm_handler(func_shutdown=None):
    """
    Docker Terminate
    https://itnext.io/containers-terminating-with-grace-d19e0ce34290
    #old - https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
    """
    import signal
    def handle_sigterm(*args):
        if callable(func_shutdown):
            func_shutdown()
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)
    #signal.signal(signal.SIGKILL, handle_sigterm)


# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    kwargs = get_args()
    logging.basicConfig(level=kwargs['log_level'])

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        log.info('start')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
