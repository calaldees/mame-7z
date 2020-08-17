import os
from collections import defaultdict
from functools import reduce
import json

import requests
import falcon

from _common.falcon_helpers import add_sink, func_path_normalizer_no_extension, update_json_handlers

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



def verify_results(archive_name, catalog, romdata):
    """
    catalog is the output form /archive/ endpoint dict(sha1, file_name) equivelent to Rom(sha1, archive_name, file_name)
    romdata is output from /sets/ dict(romsets(archive_name(missing,)))
    """
    _return = {}
    # Check archivename
    completed_archive_names = {
        _archive_name: not _data['missing']
        for _archive_name, _data in romdata['romsets'].items()
    }
    if completed_archive_names and archive_name not in completed_archive_names:
        _return['rename_archive'] = {k for k, v in completed_archive_names.items() if v}
        if len(completed_archive_names) == 1:
            archive_name = next(completed_archive_names.__iter__())
    # TODO: if the archive needs to be renamed then verification terminates. Could we proceed with the assumption of the correct archive name?
    romset = romdata['romsets'].get(archive_name)
    if not romset:
        log.warning(f'No romset data for {archive_name=}')
        return _return
    # Filenames
    def _rename_files_reducer(acc, catalog_pair):
        sha1, file_name = catalog_pair
        _expected_filename = romset['files'][sha1]
        if _expected_filename != file_name:
            acc[sha1] = {'current': file_name, 'expected': _expected_filename}
        return acc
    _return['rename_files'] = reduce(_rename_files_reducer, catalog.items(), {})
    # Missing
    def _clone_reducer(acc, missing_sha1):
        missing_filepath = romset['files'][missing_sha1]
        clone, *_file_segments = missing_filepath.split('/')
        if _file_segments:
            acc[clone].add('/'.join(_file_segments))
        else:
            acc[''].add(missing_filepath)
        return acc
    _return['missing_clones'] = reduce(_clone_reducer, romset['missing'], defaultdict(set))
    _return['missing_core'] = _return['missing_clones'].pop('', None)
    # Unknown
    _return['unknown'] = set(romdata['unknown'])
    # Move
    identified_sha1s = set(romset['matched']) | _return['unknown']
    def _move_reducer(acc, catalog_pair):
        sha1, file_name = catalog_pair
        if sha1 in identified_sha1s:
            return acc
        for _archive_name, _data in romdata['romsets'].items():
            if _archive_name in completed_archive_names:
                continue
            if sha1 in set(_data['matched']):
                acc.append((
                    dict(sha1=sha1, archive_name=archive_name, file_name=file_name),
                    dict(sha1=sha1, archive_name=_archive_name, file_name=_data['files'][sha1]),
                ))
        return acc
    _return['move'] = reduce(_move_reducer, catalog.items(), [])

    _return = {k: v for k, v in _return.items() if v}
    return _return



# ------------------------------------------------------------------------------

class VerifyResource():
    def __init__(self, get_romdata, get_catalog):
        self.get_romdata = get_romdata
        self.get_catalog = get_catalog
    def on_get(self, request, response, archive_name):
        catalog = self.get_catalog(archive_name)
        romdata = self.get_romdata(catalog.keys())
        response.media = verify_results(archive_name, catalog, romdata)
        response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(url_api_romdata, url_api_catalog, **kwargs):
    def get_catalog(archive_name):
        return requests.get(os.path.join(url_api_catalog, 'archive', archive_name)).json()
    def get_romdata(sha1s):
        return requests.get(
            os.path.join(url_api_romdata, 'sets'),
            json=tuple(sha1s),
            headers={'Content-Type': 'application/json'},
        ).json()


    app = falcon.API()
    #app.add_route(r'/', IndexResource(rom_data))
    add_sink(app, 'verify', VerifyResource(get_romdata, get_catalog), func_path_normalizer=func_path_normalizer_no_extension)
    update_json_handlers(app)
    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('--url_api_romdata', action='store', required=True, help='')
    parser.add_argument('--url_api_catalog', action='store', required=True, help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=9003, type=int, help='')

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


if __name__ == '__main__':
    #postmortem(verify_folder,'/Users/allancallaghan/Applications/mame/roms')
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
