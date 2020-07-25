import os.path
import xml.etree.ElementTree as ET
from typing import NamedTuple
from itertools import chain
import subprocess


PATH_MAME = '/Users/allancallaghan/Applications/mame/'
CMD_MAME = 'mame'


def _tag_iterator(iterparse, tag):
    for _, e in iterparse:
        if e.tag == tag:
            yield e

def _find_recursively(element, func_select):
    for child in element:
        if func_select(child):
            yield child
        else:
            yield from _find_recursively(child, func_select)


class Rom(NamedTuple):
    sha1: str
    archive_name: str
    file_name: str

    @staticmethod
    def from_xml_rom(item, rom, parent='', folder=''):
        folder_name = item.get('name') if parent else ''
        return Rom(
            sha1=rom.get('sha1'),
            archive_name=os.path.join(folder, parent or item.get('name')),
            file_name=os.path.join(folder_name, rom.get('name'))
        )

    def __str__(self) -> str:
        return f"{self.sha1} {self.archive_name}:{self.file_name}"



def _mame_xml(*args, events=('end',)):
    """
    `-listxml`
    `-getsoftlist`
    """
    assert args == ('-listxml',) or args == ('-getsoftlist',), f'{args=}'
    return ET.iterparse(
        source=subprocess.Popen(
            (CMD_MAME, *args),
            stdout=subprocess.PIPE,
            cwd=PATH_MAME,
        ).stdout,
        events=events,
    )


def _files_for_machine(machine, parents_to_exclude={}):
    if machine.get('name') in parents_to_exclude:
        return
    for rom in machine.findall('rom'):
        if rom.get('merge') or rom.get('status') == "nodump":
            continue
        yield Rom.from_xml_rom(
            item=machine,
            rom=rom,
            parent=machine.get('romof') if machine.get('romof') not in parents_to_exclude else ''
        )
def iter_mame():
    r"""
    >>> data = '''<?xml version="1.0"?>
    ... <mame build="0.222 (unknown)" debug="no" mameconfig="10">
    ...     <machine name="18wheelr" sourcefile="naomi.cpp" romof="naomi">
    ...         <rom name="epr-21576h.ic27" merge="epr-21576h.ic27" sha1="91424d481ff99a8d3f4c45cea6d3f0eada049a6d" />
    ...         <rom name="epr-22185a.ic22" sha1="2f32caf3906fc1408fd8126a500e74c682ff20fa" />
    ...     </machine>
    ...     <machine name="18wheelro" sourcefile="naomi.cpp" cloneof="18wheelr" romof="18wheelr">
    ...         <rom name="epr-21576h.ic27" merge="epr-21576h.ic27" sha1="91424d481ff99a8d3f4c45cea6d3f0eada049a6d" />
    ...         <rom name="epr-22185.ic22" sha1="6db3bfa23246c250e334bbd54dcb5038a2d18dbc" />
    ...     </machine>
    ...     <machine name="naomi" sourcefile="naomi.cpp" isbios="yes">
    ...         <rom name="epr-21576h.ic27" merge="epr-21576h.ic27" sha1="91424d481ff99a8d3f4c45cea6d3f0eada049a6d" />
    ...         <rom name="epr-22185.ic22" merge="epr-22185.ic22" sha1="6db3bfa23246c250e334bbd54dcb5038a2d18dbc" />
    ...         <rom name="epr-21576h.ic27" bios="bios0" sha1="91424d481ff99a8d3f4c45cea6d3f0eada049a6d"/>
    ...     </machine>
    ... </mame>'''.encode('utf8')
    >>> from unittest.mock import patch
    >>> with patch('subprocess.Popen') as mock_popen:
    ...    mock_popen.return_value.stdout.read.side_effect = (data, b'', data, b'')
    ...    tuple(map(str, iter_mame()))
    ('91424d481ff99a8d3f4c45cea6d3f0eada049a6d naomi:epr-21576h.ic27', '2f32caf3906fc1408fd8126a500e74c682ff20fa 18wheelr:epr-22185a.ic22', '6db3bfa23246c250e334bbd54dcb5038a2d18dbc 18wheelr:18wheelro/epr-22185.ic22')
    """
    bioss = set()
    for machine in _tag_iterator(_mame_xml('-listxml'), 'machine'):
        if machine.get('isbios') == 'yes':
            bioss.add(machine.get('name'))
            yield from _files_for_machine(machine)
    for machine in _tag_iterator(_mame_xml('-listxml'), 'machine'):
        yield from _files_for_machine(machine, parents_to_exclude=bioss)


def iter_software():
    r"""
    >>> data = '''<?xml version="1.0"?>
    ... <softwarelists>
    ...     <softwarelist name="sms" description="Sega Master System cartridges">
    ...         <software name="alexkidd">
    ...                 <part name="cart" interface="sms_cart">
    ...                         <dataarea name="rom">
    ...                             <rom name="alex kidd in miracle world (usa, europe) (v1.1).bin" sha1="6d052e0cca3f2712434efd856f733c03011be41c"/>
    ...                         </dataarea>
    ...                 </part>
    ...         </software>
    ...         <software name="alexkidd1" cloneof="alexkidd">
    ...                 <part name="cart" interface="sms_cart">
    ...                         <dataarea name="rom">
    ...                             <rom name="alex kidd in miracle world (usa, europe).bin" sha1="8cecf8ed0f765163b2657be1b0a3ce2a9cb767f4"/>
    ...                         </dataarea>
    ...                 </part>
    ...         </software>
    ...     </softwarelist>
    ... </softwarelists>'''.encode('utf8')
    >>> from unittest.mock import patch
    >>> with patch('subprocess.Popen') as mock_popen:
    ...    mock_popen.return_value.stdout.read.side_effect = (data, b'')
    ...    tuple(map(str, iter_software()))
    ('6d052e0cca3f2712434efd856f733c03011be41c sms/alexkidd:alex kidd in miracle world (usa, europe) (v1.1).bin', '8cecf8ed0f765163b2657be1b0a3ce2a9cb767f4 sms/alexkidd:alexkidd1/alex kidd in miracle world (usa, europe).bin')
    """
    iterparse = _mame_xml('-getsoftlist', events=('start', 'end'))
    current_softwarelist = ''
    for event, e in iterparse:
        if event == 'start' and e.tag == 'softwarelist':
            current_softwarelist = e.get('name')
        if event == 'end' and e.tag == 'software':
            for rom in _find_recursively(e, lambda e: e.tag == 'rom'):
                yield Rom.from_xml_rom(
                    item=e,
                    rom=rom,
                    parent=e.get('cloneof') or '',
                    folder=current_softwarelist,
                )


if __name__ == "__main__":
    for rom in chain(iter_mame(), iter_software()):
        print(rom)
