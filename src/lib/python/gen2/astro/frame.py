import os
import re
import Bunch


frame_regex = re.compile('^(\w{3})([AaQq])(\d{8})$')

class FitsFrameIdError(Exception):
    pass


def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = frame_regex.match(frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)

        frameid = frameid.upper()
        inscode = inscode.upper()
        
        return Bunch.Bunch(frameid=frameid, fitsname=fitsname,
                           fitsdir=fitsdir, inscode=inscode,
                           frametype=frametype, frame_no=frame_no)

    raise FitsFrameIdError("path does not match Subaru FITS specification: '%s'" % (
            fitspath))

#END
