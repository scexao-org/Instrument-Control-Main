from g2base.remoteObjects import remoteObjects as ro
from time import sleep
import time
import sys

# First arg is how many frameids to get. But it will only print the first one

t0 = time.time()

#gen2host = 'g2sim1.subaru.nao.ac.jp'
gen2host = 'g2ins1.sum.subaru.nao.ac.jp'

nfrmids = int(sys.argv[1])
camcode = sys.argv[2]

ro.init([gen2host])
g2proxy = ro.remoteObjectProxy('SCEXAO')

# want to allocate some frames.
g2proxy.executeCmd('SCEXAO', 'foo', 'get_frames', camcode, dict(num=nfrmids))

# frames will be stored one per line in /tmp/frames.txt
sleep(0.1)
with open("/tmp/frames_%s.txt" % (camcode, ), 'r') as in_f:
    frames = in_f.read().split('\n')
assert len(frames) > 0, Exception("Frames file is empty!")
print(frames)
print(time.time() - t0)
