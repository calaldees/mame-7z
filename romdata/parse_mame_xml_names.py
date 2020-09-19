import re

import xml.etree.ElementTree as ET
from zipfile import ZipFile

# copied from 
def _zip_filehandle(filename):
    zipfile = ZipFile(filename)
    _filename = zipfile.namelist()[0]
    filehandle = zipfile.open(_filename)
    return filehandle

def _tag_iterator(iterparse, tag):
    for _, e in iterparse:
        if e.tag == tag:
            yield e


def iter_mame_names(get_xml_filehandle):
    r"""
    >>> data = '''<?xml version="1.0"?>
    ... <mame build="0.222 (unknown)" debug="no" mameconfig="10">
    ...     <machine name="18wheelr" sourcefile="naomi.cpp" romof="naomi">
    ...         <description>18 Wheeler (deluxe, Rev A)</description>
    ...     </machine>
    ...     <machine name="18wheelro" sourcefile="naomi.cpp" cloneof="18wheelr" romof="18wheelr">
    ...         <description>18 Wheeler (deluxe)</description>
    ...     </machine>
    ...     <machine name="naomi" sourcefile="naomi.cpp" isbios="yes">
    ...         <description>Naomi BIOS</description>
    ...     </machine>
    ... </mame>'''.encode('utf8')
    >>> from unittest.mock import MagicMock
    >>> mock_filehandle = MagicMock()
    >>> mock_filehandle.return_value.read.side_effect = (data, b'')
    >>> tuple(iter_mame_names(mock_filehandle))
    (('18wheelr', '18 Wheeler (deluxe, Rev A)'),)
    """
    assert callable(get_xml_filehandle)
    for machine in _tag_iterator(ET.iterparse(get_xml_filehandle()), 'machine'):
        if machine.get('cloneof') or machine.get('isbios') == 'yes' or machine.get('isdevice') == "yes" or machine.get('runnable') == "no":
            continue
        yield (
            machine.get('name'),
            machine.find('description').text,
        )


def normalise_name(name):
    """
    >>> _n = normalise_name
    >>> _n('18 Wheeler (deluxe, Rev A)')
    '18 wheeler'
    >>> _n('Yam! Yam!?')
    'yam yam'
    >>> _n('X-Men: Children of the Atom (Euro 950331)')
    'x men children of the atom'
    >>> _n('X-Men Vs. Street Fighter (Euro 961004)')
    'x men versus street fighter'
    >>> _n('Vampire Savior 2: The Lord of Vampire (Japan 970913)')
    'vampire savior 2: the lord of vampire'
    >>> _n('U.S. Classic')
    'u s classic'
    >>> _n('Venom & Spider-Man - Separation Anxiety (SNES bootleg)')
    'venom and spider man separation anxiety'
    >>> _n('Vindicators Part II')
    'vindicators part two'
    >>> _n('Virtua Tennis 2 / Power Smash 2 (Rev A) (GDS-0015A)')
    'virtua tennis 2 / power smash 2'
    >>> _n('World Rally 2: Twin Racing')
    'world rally 2 twin racing'
    >>> _n('Xtreme Rally / Off Beat Racer!')
    'Xtreme Rally / Off Beat Racer!'
    >>> _n('Wonder Boy III - Monster Lair (set 6, World, System 16B) (8751 317-0098)')
    ''
    >>> _n('Touch & Go')
    'touch and go'
    >>> Robocop 2 (handheld)
    ''
    """
    name = name.lower()
    name = re.sub(r'\(.*\)', '', name)
    name = re.sub(r'\W', ' ', name)
    name = re.sub(r'\&', 'and', name)
    name = re.sub(r' +', ' ', name)
    name = re.sub(r' iii', ' three', name)
    name = re.sub(r' ii', ' two', name)
    name = re.sub(r' vs ', ' versus ', name)
    name = name.strip()
    return name

def main():
    for rom, name in iter_mame_names(lambda: _zip_filehandle('mamelx.zip')):
        print(f'{normalise_name(name)}:{rom}')


if __name__ == "__main__":
    #postmortem(main)
    main()