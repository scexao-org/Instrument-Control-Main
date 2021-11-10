#
# Make data directories for active instruments.  Expects env var
# DATAHOME to be set.
#
import sys, os
from cfg.INS import INSdata as INSconfig

ic = INSconfig()

for name in ic.getNames(active=True):
    dirpath = os.path.join(os.environ['DATAHOME'], name)
    if not os.path.isdir(dirpath):
        print "Making %s..." % dirpath
        os.mkdir(dirpath)

