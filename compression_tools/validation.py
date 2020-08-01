import os
import tempfile
from typing import NamedTuple

import requests

from scan import fast_scan
from p7zip import P7Zip


import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

p7zip = P7Zip()

def request_verify(roms):
    assert roms
    archive_names = {rom.archive_name for rom in roms}
    archive_name = archive_names.pop()
    assert not archive_names, 'Multiple archives to verify?'
    data = requests.get(
        'http://localhost:9001/sets',
        json=tuple(rom.sha1 for rom in roms),
    ).json()
    romset = data['romsets'].get(archive_name)
    return romset and not romset['missing'] and not data['unknown']


class Rom(NamedTuple):
    sha1: str
    archive_name: str
    file_name: str


def validate_file(f):
    log.debug(f'validating {f.relative}')
    with tempfile.TemporaryDirectory() as tempdir:
        destination_folder = os.path.abspath(os.path.join(tempdir, f.file_no_ext))
        os.makedirs(destination_folder)
        p7zip.extract(
            cwd=tempdir,
            source_file=f.abspath,
            destination_folder=destination_folder,
        )
        roms = tuple(
            Rom(
                sha1=p7zip.hash(tempdir, rom_file.abspath),
                archive_name=os.path.join(f.folder, f.file_no_ext),
                file_name=rom_file.relative
            )
            for rom_file in fast_scan(destination_folder)
        )
        return request_verify(roms)


def validate_folder(folder):
    for f in fast_scan(folder):
        if not f.exists:
            log.warning(f'{f.relative} does not exist. The file may have been removed by another thread')
            continue
        log.info(f'{f.relative}: {validate_file(f)}')


def postmortem(func, *args, **kwargs):
    import traceback
    import pdb
    import sys
    try:
        return func(*args, **kwargs)
    except Exception:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


if __name__ == '__main__':
    postmortem(validate_folder,'/Users/allancallaghan/Applications/mame/roms')
