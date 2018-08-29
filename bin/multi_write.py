#!/usr/bin/python

import os

for i in xrange(100):
    print(i)
    os.system('dm_update_channel 7 151102_offset_sky1.fits')
