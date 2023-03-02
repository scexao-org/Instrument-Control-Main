from g2base.remoteObjects import remoteObjects as ro
import sys

# Usage:
# python g2arch_archivefile.py DATAFILE FRAMEID

gen2host = 'g2sim1.subaru.nao.ac.jp'
#gen2host = 'g2ins1.sum.subaru.nao.ac.jp'

datafile = sys.argv[1]
frid = sys.argv[2]

ro.init([gen2host])
g2proxy = ro.remoteObjectProxy('SCEXAO')

# archive a file
g2proxy.executeCmd('SCEXAO', 'foo', 'archive_fits', [],
                   dict(frame_no=frid, path=datafile))
