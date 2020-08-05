import re
import os
import collections
from functools import partial
from itertools import chain
from typing import NamedTuple

import logging
log = logging.getLogger(__name__)


FileExt = collections.namedtuple('FileExt', ('filename', 'ext'))
def file_ext(filename):
    """
    >>> file_ext('test.txt')
    FileExt(filename='test', ext='txt')
    >>> file_ext('test')
    ('test', '')
    >>> file_ext('test.again.yaml')
    FileExt(filename='test.again', ext='yaml')
    >>> file_ext('.doc')
    FileExt(filename='', ext='doc')
    """
    try:
        return FileExt(*re.match('(.*)\.(.*?)$', filename).groups())
    except AttributeError:
        return (filename, '')


def file_extension_regex(exts):
    return re.compile(r'|'.join(map(lambda e: r'\.{0}$'.format(e), exts)))


def get_fileext(filename):
    try:
        return re.search(r'\.([^\.]+)$', filename).group(1).lower()
    except:
        return None


DEFAULT_IGNORE_REGEX = r'^\.|/\.|^__|/__'  # Ignore folders starting with '.' or '__' by default

def fast_scan_regex_filter(file_regex=None, ignore_regex=DEFAULT_IGNORE_REGEX):
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)
    return lambda f: file_regex.search(f) and not ignore_regex.search(f)


class FileScan(NamedTuple):
    scan_root: str
    scan_path: str
    scan_dir_entry: object
    @property
    def folder(self):
        return self.scan_path
    @property
    def file(self):
        return self.scan_dir_entry.name
    @property
    def path(self):
        return self.scan_dir_entry.path
    @property
    def abspath(self):
        return os.path.abspath(self.path)
    @property
    def relative(self):
        return self.path.replace(self.scan_root, '').strip('/')
    @property
    def ext(self):
        _, ext = file_ext(self.scan_dir_entry.name)
        return ext
    @property
    def file_no_ext(self):
        file_no_ext, _ = file_ext(self.scan_dir_entry.name)
        return file_no_ext
    @property
    def exists(self):
        return os.path.exists(self.abspath)
    @property
    def stats(self):
        return self.scan_dir_entry.stat()

def fast_scan(root, path=None, search_filter=fast_scan_regex_filter()):
    """
    >>> import tempfile
    >>> import pathlib
    >>> tempdir = tempfile.TemporaryDirectory()
    >>> for p in (map(partial(pathlib.Path, tempdir.name), (
    ...     'test/folder/1/file1.txt',
    ...     'test/folder/1/file2.txt',
    ...     'test/folder/3/file1.txt',
    ...     'test/folder/file4.json',
    ...     'file5.csv',
    ... ))):
    ...     p.parent.mkdir(parents=True, exist_ok=True)
    ...     p.touch()
    >>> files = tuple(fast_scan(tempdir.name))
    >>> sorted(f.relative for f in files)
    ['file5.csv', 'test/folder/1/file1.txt', 'test/folder/1/file2.txt', 'test/folder/3/file1.txt', 'test/folder/file4.json']
    >>> files[0].stats.st_size
    0
    >>> tempdir.cleanup()

    """
    path = path or ''
    _path = os.path.join(root, path)
    if not os.path.isdir(_path):
        log.warning(f'{path} is not an existing directory - aborting scan')
        return
    with os.scandir(_path) as scanner:
        for dir_entry in scanner:
            if (dir_entry.is_file() or dir_entry.is_symlink()):  # BUG: .is_symlink is dangerous, as symlinks can also be folders
                _filescan = FileScan(root, path, dir_entry)
                if search_filter(_filescan.relative):
                    yield _filescan
            if dir_entry.is_dir():
                yield from fast_scan(root, os.path.join(path, dir_entry.name), search_filter)
