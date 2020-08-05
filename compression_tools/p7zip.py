import os
import re
import subprocess

import logging
log = logging.getLogger(__name__)


class P7Zip():
    r"""
    Simplified opinionated wrapper for 7z

    >>> import tempfile
    >>> temp_directory1 = tempfile.TemporaryDirectory()
    >>> temp_directory2 = tempfile.TemporaryDirectory()
    >>> temp_directory3 = tempfile.TemporaryDirectory()

    >>> source_file = os.path.abspath(os.path.join(temp_directory1.name, './test/test.txt'))
    >>> os.makedirs(os.path.dirname(source_file))
    >>> with open(source_file, 'wt') as filehandle:
    ...     _ = filehandle.write('abcdefghijklmnopqrstuvwxyz\n')

    >>> P7Zip().hash(
    ...     cwd=temp_directory1.name,
    ...     source=source_file,
    ... )
    '8c723a0fa70b111017b4a6f06afe1c0dbcec14e3'

    >>> compressed_file = os.path.join(temp_directory2.name, 'test.7z')
    >>> P7Zip().compress(
    ...     cwd=temp_directory1.name,
    ...     files=('test/test.txt',),
    ...     destination_file=compressed_file,
    ... )

    >>> P7Zip().extract(
    ...     cwd=temp_directory3.name,
    ...     source_file=compressed_file,
    ... )
    >>> assert os.path.isfile(os.path.join(temp_directory3.name, 'test/test.txt'))

    >>> temp_directory1.cleanup()
    >>> temp_directory2.cleanup()
    >>> temp_directory3.cleanup()
    """

    REGEX_HASH_SHA1 = re.compile(b'[A-Fa-f0-9]{40}')

    def hash(self, cwd, source):
        """
        TODO:
        Not really effiecent as files need to be on disk - creates lots of disk IO
        Could this be replaced with a streaming version?
        We would need a way for 7z to output to file contents to stdout and pipe into python hash function
        """
        assert os.path.isfile(os.path.abspath(os.path.join(cwd, source)))
        output = subprocess.run(
            ("7z", "h", "-scrcSHA1", source),
            cwd=cwd,
            capture_output=True,
        )
        match = self.REGEX_HASH_SHA1.search(output.stdout)
        if match:
            return match.group().decode('utf8').lower()
        log.error(f'Unable to hash {source}')

    def compress(self, cwd, files, destination_file):
        destination_file = os.path.abspath(destination_file)
        assert destination_file.endswith('.7z')
        assert os.path.isdir(os.path.dirname(destination_file))
        assert not os.path.isfile(destination_file)
        for f in files:
            assert os.path.isfile(os.path.join(cwd, f))
        output = subprocess.run(
            ("7z", "a", "-t7z", "-mx=9", "-ms=on", "-md=128m", "-mmt=on", destination_file, *files),
            cwd=cwd,
            capture_output=True,
        )
        assert os.path.isfile(destination_file)

    def extract(self, cwd, source_file, destination_folder='./'):
        #assert source_file.endswith('.7z')
        assert os.path.isfile(os.path.join(cwd, source_file))
        assert os.path.isdir(os.path.join(cwd, destination_folder))
        output = subprocess.run(
            ("7z", "x", source_file, f"-o{destination_folder}"),
            cwd=cwd,
            capture_output=True,
        )
        assert len(tuple(os.scandir(os.path.abspath(os.path.join(cwd, destination_folder)))))
