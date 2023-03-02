#!/usr/env python3

''' -------------------------------------------------------------
This is a script to use in case you need to debug something
along one chain of Zaber actuators. This instance is for the
7-actuator chain.

Interactive mode is required, so run this from a ipython shell
by typing:

> ipython
In [1]: execfile('debug_zab_chain_7')

------------------------------------------------------------- '''

import sys
import os
import time
import pdb

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import zaber_chain3 as zaber

zab = zaber.zaber()
zab.open("irfront")

'''
At this point, you have an instance of zaber chain object.
You can directly send command to actuators using:

>> zab.command(id, cmd_code, cmd_argument)

List of commands are in the Zaber wiki:
http://www.zaber.com/wiki/Manuals/T-LA

Basic command codes are:
-----------------------
1. home
2. renumber
20. goto abs position
40. configure LEDs, knobs, ...

eg: 
 - zab.command(4, 1, 0)      # home actuator 4
 - zab.command(5, 20, 30000) # sends actuator 5 to position 30000
 - zab.command(6, 2, 3)      # renumbers actuator 6 as 3
 - zab.command(0, 40, 49160) # disable LEDS and knobs for all (0) actuators
 - zab.command(0, 60, 0)     # checks current position. Also lets you know Zab number
 - zab.command(0, 50, 0)     # Return device ID
 - zab.command(0, 40, 49152) # Disables LEDs only, knob active
 - zab.command(0, 40, 51214) # Disables LEDS (16 384 & 32 768), disables knob (8), antibacklash (2), antistiction (4), circular phase stepping (2048) - for bottom bench
 - zab.command(0, 40, 51208) # Disables LEDS (16 384 & 32 768), disables knob (8), circular phase stepping (2048) - for top bench

# --------------------------------------------------------------

most probable and annoying scenario is that you replaced an 
actutaor in the chain.

Procedure is:
------------
1. connect new actuator by itself to the chain.
2. delete /tmp/pci-0000:00:1a.0-usb-0:1.4.1.4:1.0-port0
3. execute this script from within a ipython session
4. the execution will stall, but will display (quiet=False) some
   info on the connected actuator. Abort with Ctrl-C
5. >> zab.close()
6. >> zab = zaber_chain.zaber_chain(zabdev, quiet=False)
   the /tmp/... file now exists so the full init is skipped
7. renumber command (see above)
8. >> zab.close()
9. exit ipython
10. rm /tmp/pci-0000:00:1a.0-usb-0:1.4.1.4:1.0-port0 (again!)
11. reconnect the full chain
12. ipython and execfile('debug_zab_chain_7')
   if all good, the execution will not stall and status info on 
   all actuators will appear.
13. zab.close()
14. exit ipython
15. pau!
# --------------------------------------------------------------
'''

