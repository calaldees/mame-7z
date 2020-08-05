import logging
import os
from typing import NamedTuple
import re
from types import MappingProxyType # https://stackoverflow.com/questions/41795116/difference-between-mappingproxytype-and-pep-416-frozendict


log = logging.getLogger(__name__)


class Rom(NamedTuple):
    sha1: str
    archive_name: str
    file_name: str

    @staticmethod
    def parse(line):
        match = re.match(
            r"""(?P<sha1>[0-9A-Fa-f]{40}) (?P<archive_name>.+):(?P<file_name>.+)""",
            line,
        )
        if match:
            return Rom(**match.groupdict())

    def __str__(self) -> str:
        return f"{self.sha1} {self.archive_name}:{self.file_name}"


# ------------------------------------------------------------------------------


class RomData():
    """
    Romdata for 364682 in python3 memory takes 185Mb RAM
    """
    def __init__(self, filehandle, readonly=True):
        if isinstance(filehandle, str):
            assert os.path.isfile(filehandle)
            filehandle = open(filehandle, 'rt')
        sha1 = {}
        archive = {}
        log.info('Loading rom data ...')
        count = 0
        for count, rom in enumerate(filter(None, map(Rom.parse, filehandle))):
            sha1.setdefault(rom.sha1, set()).add(rom)
            archive.setdefault(rom.archive_name, set()).add(rom)
            if count % 10000 == 0:
                print('.', end='', flush=True)
        print()
        log.info(f'Loaded dataset for {count} roms')
        if readonly:
            self.sha1 = MappingProxyType(sha1)
            self.archive = MappingProxyType(archive)
        filehandle.close()
