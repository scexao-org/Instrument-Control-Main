#! /usr/bin/env python
#

import sys, os, time
import myproc

Xauthority = "/gen2/conf/X/Xauthority"

dispnum = int(sys.argv[1])

# d = { 'cmd': 'Xtightvnc', 'dispnum': dispnum, 'portnum': 5900 + dispnum,
#       'xauth': Xauthority }
d = { 'cmd': '/usr/bin/Xvnc', 'dispnum': dispnum, 'portnum': 5900 + dispnum,
      'xauth': Xauthority }

# remove stale locks
try:
    os.remove('/tmp/.X%d-lock' % dispnum)
except OSError:
    pass
try:
    os.remove('/tmp/.X11-unix/X%d' % dispnum)
except OSError:
    pass

# VNC server startup command
#xsrvr_cmd = """%(cmd)s :%(dispnum)d  -desktop 'X' -auth %(xauth)s -geometry 1920x1200 -depth 24 -rfbwait 30000 -rfbauth /home2/gen2/.vnc/passwd -rfbport %(portnum)d -fp /usr/share/fonts/X11/misc/,/var/lib/defoma/x-ttcidfont-conf.d/dirs/TrueType/,/usr/share/fonts/X11/100dpi/:unscaled,/usr/share/fonts/X11/75dpi/:unscaled,/usr/share/fonts/X11/Type1/,/usr/share/fonts/X11/100dpi/,/usr/share/fonts/X11/75dpi/ -dpi 100 -AlwaysShared""" % d
xsrvr_cmd = """/usr/bin/Xvnc :%(dispnum)d -desktop X -auth %(xauth)s -geometry 1920x1200 -depth 24 -rfbwait 30000 -rfbauth /home2/gen2/.vnc/passwd -rfbport %(portnum)d -fp /usr/share/fonts/X11//misc,/usr/share/fonts/X11//Type1 -pn -AlwaysShared""" % d

# Start up the VNC server
x_proc = myproc.myproc(xsrvr_cmd)

# Wait a bit
time.sleep(2.0)

# See if it is running, if not, complain and exit
if x_proc.status() != 'running':
    print "Error starting up VNC server for display %d."
    print x_proc.output()
    sys.exit(1)

os.environ['DISPLAY'] = ':%d' % dispnum
os.environ['XAUTHORITY'] = Xauthority

# Command to set up the desktop
init_cmd = os.path.join(os.environ['HOME'], '.vnc', 'xstartup')

s_proc = myproc.myproc(init_cmd)
s_proc.wait()
print s_proc.output()

while True:
    time.sleep(60.0)

#END




