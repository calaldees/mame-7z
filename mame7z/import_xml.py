import os.path
import xml.etree.ElementTree as ET
from collections import namedtuple

import io
import subprocess


def _tag_iterator(iterparse, tag):
    for _, e in iterparse:
        if e.tag == tag:
            yield e

def _find_recursively(element, func_select):
    for child in element.getchildren():
        if func_select(child):
            yield child
        else:
            yield from _find_recursively(child, func_select)


Rom = namedtuple('Rom', ('sha1', 'archive_name', 'file_name'))
def _format_rom(item, rom, parent=''):
    folder_name = item.get('name') if parent else ''
    return Rom(
        sha1=rom.get('sha1'),
        archive_name=parent or item.get('name'),
        file_name=os.path.join(folder_name, rom.get('name'))
    )


def _mame_xml(*args, events=('end',)):
    """
    `-listxml`
    `-getsoftlist`
    """
    assert args == ('-listxml',) or args == ('-getsoftlist',), f'{args=}'
    return ET.iterparse(
        source=subprocess.Popen(
            ("mame", *args),
            stdout=subprocess.PIPE,
            cwd='/Users/allancallaghan/Applications/mame/'
        ).stdout,
        events=events,
    )

def _files_for_machine(machine, parents_to_exclude={}):
    for rom in machine.findall('rom'):
        if rom.get('merge') or rom.get('status') == "nodump":
            continue
        yield _format_rom(
            item=machine,
            rom=rom,
            parent=machine.get('romof') if machine.get('romof') not in parents_to_exclude else ''
        )

def do_mame():
    bioss = set()
    for machine in _tag_iterator(_mame_xml('-listxml'), 'machine'):
        if machine.get('isbios') == 'yes':
            bioss.add(machine.get('name'))
            yield from _files_for_machine(machine)
    for machine in _tag_iterator(_mame_xml('-listxml'), 'machine'):
        yield from _files_for_machine(machine, parents_to_exclude=bioss)



#def software_parser():
#    return ET.iterparse('/Users/allancallaghan/Applications/mame/hash/sms.xml')

def _files_for_software(current_softwarelist, element_software):
    for rom in _find_recursively(element_software, lambda e: e.tag == 'rom'):
        yield _format_rom(
            item=element_software,
            rom=rom,
            parent=element_software.get('cloneof') or ''
        )

def do_software():
    iterparse = _mame_xml('-getsoftlist', events=('start', 'end'))
    current_softwarelist = ''
    for event, e in iterparse:
        if event == 'start' and e.tag == 'softwarelist':
            current_softwarelist = e.get('name')
        if event == 'end' and e.tag == 'software':
            yield from _files_for_software(current_softwarelist, e)

    #for software in _tag_iterator(_mame_xml('-getsoftlist'), 'software'):

for f in do_software():
    print(f"{f.sha1} {f.archive_name}:{f.file_name}")
