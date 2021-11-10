#
# obsnote.py -- code to interface to the Gen2 obsnote table
#
#[ Eric Jeschke (eric@naoj.org) --
#]
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import time, datetime

# Import just what we need from config
from common import Instrument, ObsNote, Frame, \
     dbError, g2dbError, locks, session

import Bunch

def getNotesByDate(fromdate, todate):
    """Get all the notes that have been created between _fromdate_ and _todate_,
    which should be datetime objects.
    Returns a list of bunches (records) sorted by time.
    """

    # Not sure if this is tied to elixir, sqlalchemy or sqlite,
    # but it seems we have to convert python datetime objects to
    # strings of this format to compare
    fromdate = fromdate.strftime('%Y-%m-%d %H:%M:%S.%f')
    todate = todate.strftime('%Y-%m-%d %H:%M:%S.%f')
    
    with locks.obsnote:
        try:
            # Get the record from the Frame table
            obs_recs = ObsNote.query.filter(ObsNote.time_create >= fromdate).filter(ObsNote.time_create <= todate).order_by('time_create')

            # There ought to be a way to get only the attributes that
            # were defined in the schema...
            res = []
            for rec in obs_recs:
                b = Bunch.Bunch(time_create=rec.time_create,
                                time_update=rec.time_update,
                                meta=rec.meta, memo=rec.memo)
                res.append(b)
                
            # TODO: "expunge" temp records from session?
            return res

        except dbError, e:
            raise g2dbError(e)


def getNotesLastSecs(secs):
    """Get all the notes that have been created in the last _secs_ seconds.
    Returns a list of bunches (records) sorted by time.
    """
    now = datetime.datetime.now()
    before = datetime.datetime.fromtimestamp(time.time() - secs)

    return getNotesByDate(before, now)
    
def createNote(**kwdargs):
    """Create a note.  Keyword arguments should contain _meta_ and
    _memo_ which should be unicode strings.
    """

    locks.obsnote.acquire()
    rb = False
    try:
        try:
            #session.begin(subtransactions=True)
            rb = True

            # TODO: Get the records from the Frame table

            # This is the time the note was created
            create_time = datetime.datetime.now()

            # Add frame to Frames table
            note_rec = ObsNote(time_create=create_time,
                               time_update=create_time)
            #note_rec.save()

            # NOTE: No type check on values!
            d = {}
            d.update(kwdargs)
            # Make sure there are entries for meta and memo fields
            d.setdefault('meta', '')
            d.setdefault('memo', u'')

            # Make sure memo is in UTF-8
            if not isinstance(d['memo'], unicode):
                d['memo'] = unicode(d['memo'], 'utf-8')
            
            for name, val in d.items():
                setattr(note_rec, name, val)

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
            locks.obsnote.release()

# END
