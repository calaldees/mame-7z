import os
import tempfile
from typing import NamedTuple

from scan import fast_scan
from p7zip import P7Zip

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

p7zip = P7Zip()


class Rom(NamedTuple):
    sha1: str
    archive_name: str
    file_name: str


def validate_file(f):
    log.info(f'validating {f.relative}')
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
                archive_name=f.file_no_ext,
                file_name=rom_file.relative
            )
            for rom_file in fast_scan(destination_folder)
        )


def validate_folder(folder):
    for f in fast_scan(folder):
        if not f.exists:
            log.warning(f'{f.relative} does not exist. The file may have been removed by another thread')
            continue
        validate_file(f)


if __name__ == '__main__':
    validate_folder('/Users/allancallaghan/Applications/mame/roms')
