#
# frame.py -- code to interface to the Gen2 frame table
#
#[ Eric Jeschke (eric@naoj.org) --
#]
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import time, datetime, re

# Import just what we need from config
from common import Instrument, FrameMap, Frame, FrameTransfer, \
     dbError, g2dbError, locks, session

import Bunch

# String template for constructing frame ids, e.g. 'MCSA70001021'
frame_template = '%(code)3.3s%(type)1.1s%(pfx)1.1s%(num)07d'


def _get_framemap_name(insname, frtype, prefix='0'):
    with locks.frame:
        # Get the instrument record from the Instrument table
        insname = insname.upper()
        ins_rec = Instrument.query.filter(Instrument.shortname == insname).one()

        # Get the record from the FrameMap table
        frtype = frtype.upper()
        frmap_rec = FrameMap.query.join('instrument').filter(Instrument.number == ins_rec.number).filter(FrameMap.frtype == frtype).filter(FrameMap.prefix == prefix).one()

        return (ins_rec, frmap_rec)

def _get_framemap_code(inscode, frtype, prefix='0'):
    with locks.frame:
        # Get the instrument record from the Instrument table
        inscode = inscode.upper()
        ins_rec = Instrument.query.filter(Instrument.code == inscode).one()

        # Get the record from the FrameMap table
        frtype = frtype.upper()
        frmap_rec = FrameMap.query.join('instrument').filter(Instrument.number == ins_rec.number).filter(FrameMap.frtype == frtype).filter(FrameMap.prefix == prefix).one()

        return (ins_rec, frmap_rec)

def getFrameMap(insname, frtype, prefix='0'):
    with locks.frame:
        # Get FrameMap entry
        (ins_rec, frmap_rec) = _get_framemap_name(insname, frtype, prefix=prefix)

        d = { 'code': ins_rec.code,
              'type': frtype,
              'pfx' : prefix,
              'num' : frmap_rec.count }

        frameid = str(frame_template % d)
        
        return frameid


def alloc(insname, frtype, count=1, prefix='0', propid=None,
          handling=0, memo=None):
    """Get one or more frames.  Returns a list of the frame ids.
    Parameters:
    insname -- instrument name, short form (e.g. 'MOIRCS', 'SPCAM', etc.)
    frtype  -- frame type (e.g. 'A' or 'Q')
    count   -- number of desired frames (defaults to 1)
    prefix  -- prefix for frame following the frametype
                should be '0'==normal, '7'==engineering, '8'==simulator,
                '9'==summit (defaults to '0')
    propid  -- proposal id this frame was allocated under
    """
    locks.frame.acquire()

    rb = False
    try:
        try:
            #session.begin(subtransactions=True)
            rb = True

            # Get FrameMap entry
            (ins_rec, frmap_rec) = _get_framemap_name(insname, frtype, prefix=prefix)

            fr_num = frmap_rec.count

            d = { 'code': ins_rec.code,
                  'type': frtype,
                  'pfx' : prefix,
                  'num' : 0 }

            # This is the time the frames were allocated
            alloc_time = datetime.datetime.now()

            # Construct frame list
            frames = []
            for i in xrange(fr_num, fr_num+count):
                d['num'] = i
                frameid = str(frame_template % d)
                frames.append(frameid)

                # Add frame to Frames table
                frame = Frame(framemap=frmap_rec, number=i,
                              time_alloc=alloc_time, propid=propid,
                              handling=handling, memo=memo)
                # save to session
                #frame.save()
            
            # Update count in FrameMap table
            frmap_rec.count += count
            
            # Commit!
            session.commit()
            rb = False
            
            # TODO: "expunge" temp records from session?
            return frames

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        try:
            if rb:
                try:
                    session.rollback()
                except Exception, e:
                    # TODO: log exception
                    print str(e)

        finally:
            locks.frame.release()
    
def resetCount(insname, frtype, prefix, count):
    """Reset a frame counter.  Returns the frame id corresponding to the reset.
    Parameters:
    insname -- instrument name, short form (e.g. 'MOIRCS', 'SPCAM', etc.)
    frtype  -- frame type (e.g. 'A' or 'Q')
    prefix  -- prefix for frame following the frametype
                should be '0'==normal, '7'==engineering, '8'==simulator,
                '9'==summit (defaults to '0')
    count   -- desired count

    USE WITH CAUTION!!!
    """

    locks.frame.acquire()
    rb = False
    try:
        #session.begin(subtransactions=True)
        rb = True

        # Get FrameMap entry
        (ins_rec, frmap_rec) = _get_framemap_name(insname, frtype, prefix=prefix)

        # Reset count in FrameMap table
        frmap_rec.count = count

        d = { 'code': ins_rec.code,
              'type': frtype,
              'pfx' : prefix,
              'num' : count }

        frameid = str(frame_template % d)

        # Commit!
        session.commit()
        rb = False

        # TODO: "expunge" temp records from session?

        return frameid

    finally:
        try:
            if rb:
                try:
                    session.rollback()
                except Exception, e:
                    # TODO: log exception
                    print str(e)

        finally:
            locks.frame.release()
    

def getFrame(frameid, **kwdargs):
    """Returns a frame record from the Frame table matching frameid.
    """

    match = re.match('^(\w{3})([AQ])(\d)(\d{7})$', frameid)
    if not match:
        raise g2dbError("Bad frameid '%s'" % frameid)

    (inscode, frtype, prefix, number) = match.groups()

    locks.frame.acquire()
    try:
        try:
            # Get the record from the Frame table
            ins_rec, frmap_rec = _get_framemap_code(inscode, frtype, prefix)
            
            # Get the record from the Frame table
            fr_rec = Frame.query.filter(Frame.number == number).filter(Frame.framemap == frmap_rec).one()

            return fr_rec

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        locks.frame.release()


def getInfo(frameid, **kwdargs):

    locks.frame.acquire()
    rb = False
    try:
        try:
            #session.begin(subtransactions=True)
            #rb = True

            fr_rec = getFrame(frameid)

            # There ought to be a way to get only the attributes that
            # were defined in the schema...
            frameid = str(fr_rec)
#            res = Bunch.Bunch(frameid=frameid, time_alloc=fr_rec.time_alloc,
#                              handling=fr_rec.handling, memo=fr_rec.memo)

            res = Bunch.Bunch(frameid=frameid, time_alloc=fr_rec.time_alloc,
                              handling=fr_rec.handling, meta=fr_rec.meta)


            # Commit!

            #session.commit()
            rb = False
            
            # TODO: "expunge" temp records from session?

            return res

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        try:
            if rb:
                try:
                    session.rollback()
                except Exception, e:
                    # TODO: log exception
                    print str(e)

        finally:
            locks.frame.release()


def setInfo(frameid, **kwdargs):

    locks.frame.acquire()
    rb = False
    try:
        try:
            #session.begin(subtransactions=True)
            rb = True

            fr_rec = getFrame(frameid)

            # NOTE: No type check on values!
            for name, val in kwdargs.items():
                setattr(fr_rec, name, val)
                
            # Commit!
            session.commit()
            rb = False

            # TODO: "expunge" temp records from session?

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        try:
            if rb:
                try:
                    session.rollback()
                except Exception, e:
                    # TODO: log exception
                    print str(e)

        finally:
            locks.frame.release()

def getXfer(frameid):
    """Returns all records from the FrameTransfer table matching frameid.
       this function is used in cleanup-fits process
    """

    locks.frame.acquire()
    try:
        fr_rec = getFrame(frameid)
        xfer_recs = FrameTransfer.query.filter(FrameTransfer.frame == fr_rec).all()
    except Exception:
        xfer_recs = []
    finally:
        locks.frame.release()
        return xfer_recs

def getTransfers(frameid):
    """Returns all records from the FrameTransfer table matching frameid.
    """

    locks.frame.acquire()
    try:
        fr_rec = getFrame(frameid)

        try:
            # Get the records from the FrameTransfer table
            #xfer_recs = FrameTransfer.query.filter(FrameTransfer.id == fr_rec.id).all()
            xfer_recs = FrameTransfer.query.filter(FrameTransfer.frame == fr_rec).all()

            return xfer_recs

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        locks.frame.release()


def addTransfer(frameid, **paramDict):

    locks.frame.acquire()

    rb = False
    try:
        try:
            #session.begin(subtransactions=True)
            rb = True

            # Get Frame entry
            fr_rec = getFrame(frameid)

            # Add entry to FrameTransfer table
            xfer_rec = FrameTransfer(frame=fr_rec, **paramDict)

            # save to session
            #xfer_rec.save()
            
            # Commit!
            session.commit()
            rb = False
            
            # TODO: "expunge" temp records from session?
            return xfer_rec

        except dbError, e:
            raise g2dbError(e)
        
    finally:
        try:
            if rb:
                try:
                    session.rollback()
                except Exception, e:
                    # TODO: log exception
                    print str(e)

        finally:
            locks.frame.release()


def getFramesByDate(fromdate, todate, no_time_xfer=False, no_time_saved=False,
                    no_time_hilo=False, skip_cancel=False):
    """Get all the frames that were allocated between _fromdate_ and _todate_,
    which should be datetime objects.
    Returns a list of bunches (records) sorted by time.
    """

    with locks.frame:
        try:
            print "1"
            # Get the records from the Frame table matching selected dates
            fr_recs = Frame.query.filter(Frame.time_alloc >= fromdate).filter(Frame.time_alloc <= todate)

            print "2"
            # Order by time of allocation
            fr_recs = fr_recs.order_by('time_alloc').all()

            res = []
            # For each frame
            for fr_rec in fr_recs:
                b = Bunch.Bunch(frameid=str(fr_rec),
                                time_alloc=fr_rec.time_alloc,
                                time_xfer=None, time_saved=None,
                                time_hilo=None, time_stars=None)
                res.append(b)

                print "3"
                # Get the transfer records corresponding to this frame
                tr_recs = FrameTransfer.query.filter(FrameTransfer.frame == fr_rec)
                tr_recs = tr_recs.order_by('time_done').all()

                # Iterate over the transfer records, looking for special ones
                for rec in tr_recs:
                    trtype = rec.xfer_type
                    if not trtype:
                        continue
                    trtype = trtype.strip()

                    if trtype == 'inst->gen2':
                        b.setvals(time_xfer=rec.time_start,
                                  time_saved=rec.time_done,
                                  time_hilo=rec.time_done)
                    elif trtype == 'gen2->stars':
                        print "found stars"
                        b.setvals(time_stars=rec.time_done)
                
            # TODO: "expunge" temp records from session?
            print "4"
            return res

        except dbError, e:
            raise g2dbError(e)


def getFramesLastSecs(secs):
    """Get all the frames that have been allocated in the last _secs_ seconds.
    Returns a list of bunches (records) sorted by time.
    """
    now = datetime.datetime.now()
    before = datetime.datetime.fromtimestamp(time.time() - secs)

    return getFramesByDate(before, now)


## def getAllFrames():
##     with locks.frame:
##         try:
##             # Get the record from the Frame table
##             fr_recs = Frame.query.all().order_by('time_alloc')

##             # There ought to be a way to get only the attributes that
##             # were defined in the schema...
##             res = []
##             for rec in fr_recs:
##                 frameid = str(rec)
##                 b = Bunch.Bunch(frameid=frameid, time_alloc=rec.time_alloc,
##                                 time_saved=rec.time_saved,
##                                 time_hilo=rec.time_hilo,
##                                 time_xfer=rec.time_xfer,
##                                 time_delete=rec.time_delete,
##                                 time_tape=rec.time_tape)
##                 res.append(b)
                
##             # TODO: "expunge" temp records from session?
##             return res

##         except dbError, e:
##             raise g2dbError(e)


# END
