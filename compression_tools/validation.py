import tempfile

from scan import fast_scan


def validate(folder):
    for f in fast_scan(folder):
        print(f.abspath)


if __name__ == '__main__':
    validate('/Users/allancallaghan/Applications/mame/roms')
