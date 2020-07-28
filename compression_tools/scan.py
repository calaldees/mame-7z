import re
import os
import collections
from functools import partial
from itertools import chain

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


FileScan = collections.namedtuple('FileScan', ('folder', 'file', 'path', 'abspath', 'relative', 'stats', 'ext', 'file_no_ext'))
def fast_scan(root, path=None, search_filter=fast_scan_regex_filter()):
    path = path or ''
    with os.scandir(os.path.join(root, path)) as scanner:
        for dir_entry in scanner:
            _relative = dir_entry.path.replace(root, '').strip('/')
            if (dir_entry.is_file() or dir_entry.is_symlink()) and search_filter(_relative):  # .is_symlink is dangerious, as symlinks can also be folders
                file_no_ext, ext = file_ext(dir_entry.name)
                yield FileScan(
                    folder=path,
                    file=dir_entry.name,
                    path=dir_entry.path,
                    abspath=os.path.abspath(dir_entry.path),
                    relative=_relative,
                    stats=dir_entry.stat(),
                    ext=ext,
                    file_no_ext=file_no_ext,
                )
            if dir_entry.is_dir():
                for sub_dir_entry in fast_scan(root, os.path.join(path, dir_entry.name), search_filter):
                    yield sub_dir_entry
