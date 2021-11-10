import pyfits
import os.path
import astro.fitsutils as fitsutils

fromdir = '/gen2/data/tmp/spcam'
todir   = '/gen2/data/tmp/new'

startframe = 1354880

with open('frames.txt', 'r') as in_f:
    buf = in_f.read()

lines = buf.split('\n')

framecount = startframe
for frameid in lines:
    if len(frameid) == 0:
        continue
    if frameid.startswith('#'):
        continue

    path = os.path.join(fromdir, frameid + '.fits')
    tup = fitsutils.getFrameInfoFromPath(path)
    (frameid, fitsname, fitsdir, inscode, frametype, frame_no) = tup

    expid = int(str(framecount)[:-1] + '0')
    newframeid = "%3.3s%1.1s%08d" % (inscode, frametype, framecount)
    updateDict = { 'FRAMEID': newframeid,
                   'EXP-ID': "%3.3sE%08d" % (inscode, expid),
                   }

    newpath = os.path.join(todir, newframeid + '.fits')
    print "updating old(%s) new(%s) dict=%s" % (
        path, newpath, updateDict)

    fitsobj = pyfits.open(path, 'readonly')
    try:
        for hdu in fitsobj:
            for (kwd, val) in updateDict.items():
                hdu.header.update(kwd, val)

            hdu.scale('int16', '', bzero=32768)
        fitsobj.writeto(newpath)
            
    finally:
        fitsobj.close()
    

    framecount += 1

