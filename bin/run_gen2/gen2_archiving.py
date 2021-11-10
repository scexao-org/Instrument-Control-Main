#!/usr/bin/env python

from g2base.remoteObjects import remoteObjects as ro
from time import sleep
import time, sys, glob, os
from datetime import datetime
from astropy.io import fits as pf


def gen2_getframeids(g2proxy, camcode, nfrmids):

    # want to allocate some frames.
    g2proxy.executeCmd('SCEXAO', 'foo', 'get_frames', camcode, dict(num=nfrmids))
    
    # frames will be stored one per line in /tmp/frames.txt
    sleep(0.1)
    with open("/tmp/frames_%s.txt" % (camcode,), 'r') as in_f:
        frames = in_f.read().split('\n')
    assert len(frames) > 0, Exception("Frames file is empty!")
    return frames

def gen2_archive(frameids,directory):
    
    for i in range(len(frameids)):
        g2proxy.executeCmd('SCEXAO', 'foo', 'archive_fits', [], dict(frame_no=frameids[i], path="%s/%s.fits"%(directory, frameids[i])))

    
if __name__ == "__main__":

    #gen2host = 'g2sim1.subaru.nao.ac.jp'
    gen2host = 'g2ins1.sum.subaru.nao.ac.jp'
    
    ro.init([gen2host])
    g2proxy = ro.remoteObjectProxy('SCEXAO')
    monitored = ["kcam"]
    camids = {"kcam":"B", "ircam0":"C","first":"F","glint":"G","renocam":"P","ircam1":"R","vcam":"V"}
    directory = "/media/data/ARCHIVED_DATA"
    notdone = True

    while True:

        dateutc = datetime.utcnow().strftime("%Y%m%d")
        ntot = 0
        directory2 = "%s/%s" %(directory,dateutc)
        if os.path.exists(directory2):
            #list all new monitored cubes
            for i in range(len(monitored)):
                # List all the new files 
                cubelist = glob.glob("%s/%slog/%s*.fits" %(directory2, monitored[i], monitored[i]))
                cubelist.sort()
                ncubes = len(cubelist)
                ntot += ncubes
                print(ntot)
                time.sleep(2)

                
                if ncubes > 0:
                    # Get frames IDs for all the new cubes from camera monitored[i]
                    frameids = gen2_getframeids(g2proxy, camids[monitored[i]], ncubes)

                    for j in range(ncubes):
                        # change the FRAMID keyword for the Subaru-compliant frame ID
                        while notdone:
                            try:
                                pf.setval(cubelist[j],"FRAMEID",value=frameids[j],savecomment=True)
                                notdone = False
                            except:
                                time.sleep(1)
                                notdone = True
                        notdone = True
                        # Rename the file with the frame ID
                        pathc, oldname = os.path.split(cubelist[j])
                        newname = "%s.fits" % (frameids[j],)
                        os.rename(cubelist[j],"%s/%s" %(pathc,newname))
                        # Log the name change
                        with open("%s/name_changes.txt" %(pathc,), "a") as namelog:
                            namelog.write("%s\t%s \n" %(oldname,newname))
                            namelog.close()
                        # Archive file
                        g2proxy.executeCmd('SCEXAO', 'foo', 'archive_fits', [], dict(frame_no=frameids[j], path="%s/%s"%(pathc,newname)))
                        print("logging %s -> %s" %(oldname,newname))

            if ntot == 0:
                # Wait for new files to appear 
                print("waiting for new file")
                time.sleep(1)

        
        else:
            # Wait for the folder to be created
            print("waiting for new directory")
            time.sleep(10)
