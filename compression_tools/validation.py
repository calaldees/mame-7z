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


class Rom(NamedTuple):
    sha1: str
    archive_name: str
    file_name: str


def validate_archive(f):
    archive_name = os.path.join(f.folder, f.file_no_ext)
    log.debug(f'validating {archive_name} {f.relative}')
    with tempfile.TemporaryDirectory() as tempdir:
        # Extract Archive - to tempdir
        destination_folder = os.path.abspath(os.path.join(tempdir, archive_name))
        os.makedirs(destination_folder)
        p7zip.extract(
            cwd=tempdir,
            source_file=f.abspath,
            destination_folder=destination_folder,
        )
        # Hash check archive content as Rom list
        roms = tuple(
            Rom(
                sha1=p7zip.hash(tempdir, rom_file.abspath),
                archive_name=archive_name,
                file_name=rom_file.relative,
            )
            for rom_file in fast_scan(destination_folder)
        )
    # Verify roms
    data = requests.get(
        'http://localhost:9001/sets',
        json=tuple(rom.sha1 for rom in roms),
    ).json()
    romset = data['romsets'].get(archive_name)
    return romset and not romset['missing'] and not data['unknown']
    # TODO:
    # incorrect rom name (check)
    # incorrect archive_name? core+archive_name?
    # missing
    #  clone
    # uneeded file
    # file from another romset
    # ok core - ok clones


def validate_folder(folder):
    for f in fast_scan(folder):
        if not f.exists:
            log.warning(f'{f.relative} does not exist. The file may have been removed by another thread')
            continue
        is_valid = validate_archive(f)
        log.info(f'{f.relative}: {is_valid=}')


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
