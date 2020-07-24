import os.path
import xml.etree.ElementTree as ET
from functools import reduce

def mame_parser():
    return ET.iterparse('/Users/allancallaghan/Applications/mame/mame.xml')

#def reduce_bios(bioss, i):
#    _, e = i
#    if e.tag == 'machine' and e.get('isbios') == 'yes':
#        bioss.add(e.get('name'))
#    return bioss
#bioss = reduce(reduce_bios, mame_parser(), set())


def machine_iterator():
    for _, e in mame_parser():
        if e.tag == 'machine':
            yield e


def print_roms_for_machine(machine):
    for rom in machine.findall('rom'):
        if rom.get('merge') or rom.get('status') == "nodump":
            continue
        parent = machine.get('romof') if machine.get('romof') not in bioss else ''
        archive_name = parent or machine.get('name')
        folder_name = machine.get('name') if parent else ''
        file_name = os.path.join(folder_name, rom.get('name'))
        sha1 = rom.get('sha1')
        assert sha1
        print(f"{sha1} {archive_name}:{file_name}")


bioss = set()
for machine in machine_iterator():
    if machine.get('isbios') == 'yes':
        bioss.add(machine.get('name'))
        print_roms_for_machine(machine)

#bioss = {'isgsm', '3dobios', 'coh1000a', 'coh1002e', 'coh1002m', 'taitotz', 'allied', 'coh3002t', 'chihiro', 'kviper', 'f355bios', 'segasp', 'gp_110', 'konamigv', 'cdibios', 'gts1s', 'hng64', 'megaplay', 'aristmk5', 'lindbios', 'mac2bios', 'coh1000t', 'bubsys', 'su2000', 'coh3002c', 'decocass', 'macsbios', 'pyson', 'shtzone', 'maxaflex', 'f355dlx', 'gts1', 'ar_bios', 'aristmk6', 'naomi2', 'coh1001l', 'hod2bios', 'coh1000c', 'awbios', 'alg3do', 'galgbios', 'gq863', 'nichidvd', 'megatech', 'sfcbox', 'konamigx', 'naomi', 'sys246', 'naomigd', 'cubo', 'cedmag', 'alg_bios', 'iteagle', 'pgm', 'sys256', 'triforce', 'v4bios', 'nss', 'airlbios', 'skns', 'coh1000w', 'konendev', 'neogeo', 'atarisy1', 'playch10', 'sys573', 'coh1002v', 'crysbios', 'aleck64', 'tourvis', 'hikaru', 'stvbios', 'sammymdl'}


for machine in machine_iterator():
    print_roms_for_machine(machine)
