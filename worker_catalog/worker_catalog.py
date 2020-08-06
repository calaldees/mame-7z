import os
import logging
import pathlib
import datetime
import tempfile
import time

import requests

from _common.scan import fast_scan
from _common.p7zip import P7Zip


log = logging.getLogger(__name__)
p7zip = P7Zip()


def hash_archive(rom_path, archive):
    archive_name = os.path.join(archive.parent.name, archive.stem)
    log.debug(f'hashing {archive_name}')
    with tempfile.TemporaryDirectory() as tempdir:
        # Extract Archive - to tempdir
        destination_folder = os.path.abspath(os.path.join(tempdir, archive_name))
        os.makedirs(destination_folder)
        p7zip.extract(
            cwd=tempdir,
            source_file=rom_path.joinpath(archive).resolve,
            destination_folder=destination_folder,
        )
        # Hash check archive content as Rom list
        return tuple(
            dict(
                sha1=p7zip.hash(tempdir, rom_file.abspath),
                archive_name=archive_name,
                file_name=rom_file.relative,
            )
            for rom_file in fast_scan(destination_folder)
        )


def worker_catalog(rom_path, url_api_catalog, sleep, **kwags):
    while True:
        _file = requests.get(f'{url_api_catalog}/next_file').json['file']
        if not _file:
            time.sleep(sleep)
            continue
        roms = hash_archive(rom_path, pathlib.Path(_file))
        requests.post(f'{url_api_catalog}/archive/{_file}', json=roms)


def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('rom_path', action='store', default='', help='')
    parser.add_argument('url_api_catalog', action='store', default='', help='')

    parser.add_argument('--sleep', action='store', type=int, default=60)
    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    kwargs = vars(parser.parse_args())

    kwargs['rom_path'] = pathlib.Path(kwargs['rom_path'])
    kwargs['sleep'] = datetime.timedelta(seconds=kwargs['sleep'])
    return kwargs


if __name__ == '__main__':
    kwargs = get_args()
    logging.basicConfig(level=kwargs['log_level'])
    worker_catalog(**kwargs)
