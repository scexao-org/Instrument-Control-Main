"""
Author: Alex Walter
Date: Aug 29, 2018
This code is for dithering the Newport Conex-AG-M100D stage in the MEC fore-optics
"""
from __future__ import print_function
import serial
import time
import numpy as np
from threading import RLock, Thread
import itertools
import argparse
import requests
import os
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library


TIMEOUT = 2.25
CONEX_PORT = 50001

class ConexStatus(object):
    def __init__(self, state='offline', pos=(np.nan, np.nan), conexstatus='', limits=None):
        """
            state is a ConexManager state : 'idle' 'offline' 'processing' 'stopped/stopping'
                                         'moving to {}, {}'
                                         'move to {:.2f}, {:.2f} failed'
            pos is the (x,y) pos (nan nan) if issues
            limits are the conex limits (a dict umin umax vmin vmax)
            conexstatus is the conex result of TS or ''
        """
        self.state = state
        self.pos = pos
        self.conexstatus = conexstatus
        self.limits = limits

    def __eq__(self, o):
        return (self.state == o.state and self.pos == o.pos and self.conexstatus == o.conexstatus and
                self.limits == o.limits)

    @property
    def xpos(self):
        return self.pos[0]

    @property
    def ypos(self):
        return self.pos[1]

    @property
    def running(self):
        return 'moving' in self.state or 'processing' in self.state

    @property
    def haserrors(self):
        return 'error' in self.state

    @property
    def offline(self):
        return 'offline' in self.state

    def __str__(self):
        return self.state

    def show(self):
        print(self.state)
        print(self.pos)
        print(self.conexstatus)

def move(x, y, devname = 'steering', address='http://localhost:50001', timeout=TIMEOUT):
    try:
        r = requests.post(address+'/move', json={'x': x, 'y': y}, timeout=timeout)
        if r.status_code == 400:
            return ConexStatus(state='error: "{}"'.format(r.json()))
        j = r.json()
        ret = ConexStatus(state=j['state'], pos=(j['xpos'],j['ypos']), conexstatus=j['conexstatus'])
        if devname == "steering":
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['ypos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['xpos'])])
        else:
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['xpos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['ypos'])])
            
    except requests.ConnectionError:
        ret = ConexStatus(state='error: unable to connect')
    except ValueError:
        ret = ConexStatus(state='error: malformed content "{}"'.format(r.text))
    return ret

def full_status(devname = 'steering', address='http://localhost:50001', timeout=TIMEOUT):
    try:
        r = requests.get(address + '/conex', timeout=timeout)
        j = r.json()
        ret = ConexStatus(state=j['state'], pos=(j['xpos'],j['ypos']), conexstatus=j['conexstatus'])
        if devname == "steering":
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['ypos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['xpos'])])
        else:
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['xpos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['ypos'])])
    
    except requests.ConnectionError:
        ret = ConexStatus(state='error: unable to connect')
    except ValueError:
        ret = ConexStatus(state='error: malformed content "{}"'.format(r.text))
    return ret

def status(devname = 'steering', address='http://localhost:50001', timeout=TIMEOUT):
    try:
        r = requests.get(address + '/conex', timeout=timeout)
        j = r.json()
        if devname == "steering":        
            pos=(j['xpos'],j['ypos'])
        else:
            pos=(j['ypos'],j['xpos'])
    
        if devname == "steering":
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['ypos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['xpos'])])
        else:
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['xpos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['ypos'])])
    except requests.ConnectionError:
        ret = ConexStatus(state='error: unable to connect')
    except ValueError:
        ret = ConexStatus(state='error: malformed content "{}"'.format(r.text))
    return pos

def stop(devname = 'steering', address='http://localhost:50001', timeout=TIMEOUT):
    try:
        r = requests.post(address + '/conex', json={'command': 'stop'}, timeout=timeout)
        if r.status_code == 400:
            return ConexStatus(state='error: "{}"'.format(r.json()))
        j = r.json()
        ret = ConexStatus(state=j['state'], pos=(j['xpos'], j['ypos']), conexstatus=j['conexstatus'])
        if devname == "steering":
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['ypos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['xpos'])])
        else:
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_theta", str(j['xpos'])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_phi", str(j['ypos'])])

    except requests.ConnectionError:
        ret = ConexStatus(state='error: unable to connect')
    except ValueError:
        ret = ConexStatus(state='error: malformed content "{}"'.format(r.text))
    return ret

