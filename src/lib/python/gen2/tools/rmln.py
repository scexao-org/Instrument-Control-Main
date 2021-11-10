#! /usr/bin/env python
#
# Eric Jeschke  2011-07-06
#
"""
Remove a line from an ASCII file.

Usage:
  rmln.py <file> <lineno>

File is backed up as <file>.bak
"""

import sys, os

oldname = sys.argv[1]
newname = oldname + '.new'
bakname = oldname + '.bak'
lineno = int(sys.argv[2])

st = os.stat(oldname)

with open(oldname, 'r') as in_f:
    lines = in_f.read().split('\n')

newlines = lines[0:lineno-1] + lines[lineno:]
buf = '\n'.join(newlines) + '\n'

if os.path.exists(bakname):
    os.remove(bakname)

with open(newname, 'w') as out_f:
    out_f.write(buf)

os.chmod(newname, st.st_mode)

os.rename(oldname, bakname)
os.rename(newname, oldname)

#END


