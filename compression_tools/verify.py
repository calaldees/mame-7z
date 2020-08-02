import os
import tempfile
from typing import NamedTuple
from functools import reduce
from collections import defaultdict

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


def verify_results(archive_name, roms, data):
    _return = {}
    # Check archivename
    completed_archive_names = {
        _archive_name: not _data['missing']
        for _archive_name, _data in data['romsets'].items()
    }
    if completed_archive_names and archive_name not in completed_archive_names:
        log.debug(f'incorrect_archivename: {archive_name} -> {completed_archive_names}')
        _return['rename_archive'] = {k for k, v in completed_archive_names.items() if v}
        if len(completed_archive_names) == 1:
            archive_name = next(completed_archive_names.__iter__())
    # TODO: if the archive needs to be renamed then verification terminates. Could we proceed with the assumption of the correct archive name?
    romset = data['romsets'].get(archive_name)
    if not romset:
        return _return
    # Filenames
    def _rename_files_reducer(acc, rom):
        _expected_filename = romset['files'][rom.sha1]
        if _expected_filename != rom.file_name:
            acc[rom.sha1] = {'current': rom.file_name, 'expected': _expected_filename}
        return acc
    _return['rename_files'] = reduce(_rename_files_reducer, roms, {})
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
    _return['unknown'] = set(data['unknown'])
    # Move
    identified_sha1s = set(romset['matched']) | _return['unknown']
    def _move_reducer(acc, rom):
        if rom.sha1 in identified_sha1s:
            return acc
        for _archive_name, _data in data['romsets'].items():
            if _archive_name in completed_archive_names:
                continue
            if rom.sha1 in set(_data['matched']):
                acc.append((rom, Rom(rom.sha1, _archive_name, _data['files'][rom.sha1])))
        return acc
    _return['move'] = reduce(_move_reducer, roms, [])

    _return = {k: v for k, v in _return.items() if v}
    return _return


def verify_archive(f):
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
    data = requests.get('http://localhost:9001/sets', json=tuple(rom.sha1 for rom in roms)).json()
    return verify_results(archive_name, roms, data)



def verify_folder(folder):
    for f in fast_scan(folder):
        if not f.exists:
            log.warning(f'{f.relative} does not exist. The file may have been removed by another thread')
            continue
        is_valid = verify_archive(f)
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
    postmortem(verify_folder,'/Users/allancallaghan/Applications/mame/roms')
