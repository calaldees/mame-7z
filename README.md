mame-7z
=======
A ROM manager for MAME that maintains 7z solid archives


Notes
-----

https://github.com/SabreTools/SabreTools/wiki/DAT-File-Formats

https://mamedev.emulab.it/etabeta/2010/05/11/documenting-software-at-last/

https://docs.mamedev.org/commandline/commandline-all.html
-listdevices
-listslots

7z not working for software
https://forums.bannister.org/ubbthreads.php?ubb=showflat&Number=91921

hash xml files in mame repo
https://forums.bannister.org/ubbthreads.php?ubb=showflat&Main=8986&Number=115643
https://git.redump.net/mame/tree/hash
https://github.com/mamedev/mame/tree/mame0222/hash

```bash
# https://sevenzip.osdn.jp/chm/cmdline/switches/method.htm
7z a out.7z ./in -t7z -mx=9 -ms=on -md=128m -mmt=on

~/Applications/mame$ 7z h -scrcSHA1 software/sms/alexkidd.7z
```
