import os
import re
import subprocess

import logging
log = logging.getLogger(__name__)


class P7Zip():
    """
    Simplified opinionated wrapper for 7z
    """

    REGEX_HASH_SHA1 = re.compile(b'[A-Fa-f0-9]{40}')

    def __init__(self):
        pass

    def hash(self, source):
        """
        >>> P7Zip().hash('./test/test.txt')
        '8c723a0fa70b111017b4a6f06afe1c0dbcec14e3'
        """
        assert os.path.isfile(source)
        output = subprocess.run(
            ("7z", "h", "-scrcSHA1", source),
            capture_output=True,
        )
        match = self.REGEX_HASH_SHA1.search(output.stdout)
        if match:
            return match.group().decode('utf8').lower()
        log.error(f'Unable to hash {source}')

    def compress(self, cwd, files, destination_file):
        """
        files relative to cwd
        """
        destination_file = os.path.abspath(destination_file)
        assert destination_file.endswith('.7z')
        assert os.path.isdir(os.path.basename(destination_file))
        for f in files:
            assert os.path.isfile(os.path.join(cwd, f))
        output = subprocess.run(
            ("7z", "a", "-t7z" "-mx=9", "-ms=on", "-md=128m", "-mmt=on", destination_file, *files),
            cwd=cwd,
            capture_output=True,
        )

    def extract(self, cwd, source_file, destination_folder):
        assert source_file.endswith('.7z')
        assert os.path.isfile(os.path.join(cwd, source_file))
        assert os.path.isdir(os.path.join(cwd, destination_folder))
        output = subprocess.run(
            ("7z", "x", source_file, destination_folder),
            cwd=cwd,
            capture_output=True,
        )
        assert len(os.scandir(os.path.join(cwd, destination_folder)))
