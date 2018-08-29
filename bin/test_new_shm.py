#!/usr/bin/env python

import pygame, sys
from pygame.locals import *
import numpy as np
import matplotlib.cm as cm
import struct 
import os
import Image
import time
import math as m
import copy
import datetime as dt
from astropy.io import fits as pf
import matplotlib.pyplot as plt

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import colormaps as cmaps
from scexao_shm_new import shm

cam = shm("/tmp/ims1.im.shm", verbose=True)

temp =  cam.get_data(False, False, timeout=1.0).astype('float')
temp2 = temp.reshape(256, 320)

plt.ion()

plt.figure()

plt.imshow(temp2)
