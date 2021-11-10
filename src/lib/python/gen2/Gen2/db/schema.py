#
# schema.py -- schema for tables used in Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 10 09:00:07 HST 2012
#]
#

# Elixir is a thin declarative layer on top of SQLAlchemy
# Ubuntu: apt-get install python-sqlalchemy python-elixir
from elixir import *

# Follows the design pattern often called "ActiveRecord", where you
# define a Python class for each kind of entity.


class Instrument(Entity):
    """Defines an instrument.
    """
    using_options(tablename='instrument')

    # Canonical number of the instrument 
    number = Field(Integer, primary_key=True)

    # Short instrument name (e.g. "MOIRCS", "SPCAM")
    shortname = Field(String(30))

    # Full instrument name (e.g. "MOIRCS", "Suprime Cam")
    fullname = Field(String(60))

    # 3-letter instrument code (e.g. "MCS", "SUP")
    code = Field(String(3))

    # Year instrument began first use in OCS
    year = Field(Integer)

    # General description of the instrument
    description = Field(Unicode(256))

    # Free-form ASCII metadata
    meta = Field(String(2000))


    def __str__(self):
        return self.shortname

    def __repr__(self):
        return '<Instrument "%s" (%s:%d)>' % (self.shortname, self.code,
                                              self.number)


class FrameMap(Entity):
    """Defines a entity that a frame belongs to.  Consists of an instrument,
    a type (A or Q), a prefix (0, 7, 8, or 9) and a count (current counter).
    """
    using_options(tablename='framemap')

    # For which instruments
    instrument = ManyToOne('Instrument', required=True, primary_key=True)

    # "A" or "Q"
    frtype = Field(String(1), primary_key=True)
    
    # prefix: "8", "9" or "0"
    prefix = Field(String(1), primary_key=True)
    
    # Count
    count = Field(Integer)

    def get_pfx(self):
        return '%3.3s%1.1s%1.1s' % (self.instrument.code, self.frtype,
                                    self.prefix)
    def __str__(self):
        return '%s%07d' % (self.get_pfx(), self.count)

    def __repr__(self):
        return '<FrameMap %s:%d>' % (self.get_pfx(), self.count)


class Frame(Entity):
    """Defines an entity for a frame.  A frame belongs to a framemap entry,
    and has a number and time of allocation.
    """
    using_options(tablename='frame')

    # For which instrument (e.g. 'MSCA0')
    framemap = ManyToOne('FrameMap', required=True, primary_key=True)

    # Count (last 7 digits of frameid)
    number = Field(Integer, primary_key=True)

    # Proposal id this frame was allocated under
    propid = Field(String(6))
    
    # Time allocated
    time_alloc = Field(DateTime)

    # How should this frame be handled
    handling = Field(Integer)
    
    # Free-form metadata content
    meta = Field(String(500))

    def __str__(self):
        return '%5.5s%07d' % (str(self.framemap.get_pfx()), self.number)
    def __repr__(self):
        return '<Frame %s:%d>' % (str(self.framemap.get_pfx()), self.number)


class FrameTransfer(Entity):
    """Defines an entity for a frame transfer operation.
    """
    using_options(tablename='frametransfer')

    # For which frame
    frame = ManyToOne('Frame', required=True)

    # Source host
    src_host = Field(String(64))
    
    # Source path
    src_path = Field(String(1024))
    
    # Destination host
    dst_host = Field(String(64))
    
    # Destination path
    dst_path = Field(String(1024))
    
    # Transfer method
    xfer_method = Field(String(12))

    # Transfer command
    xfer_cmd = Field(String(1024))

    # Transfer result code
    xfer_code = Field(Integer)

    # Transfer type
    xfer_type = Field(String(12))

    # Time file transfer was initiated
    time_start = Field(DateTime)

    # Time file received successfully
    time_done = Field(DateTime)

    # Overall result code
    res_code = Field(Integer)

    # Result or error string
    res_str = Field(String(512))

    # MD5 sum
    md5sum = Field(String(32))

    # Free-form ASCII metadata
    meta = Field(String(500))

    def __str__(self):
        return '<Transfer %s>' % (self.frame)
    def __repr__(self):
        return '<Transfer %s>' % (self.frame)


class ObsNote(Entity):
    """Defines an entity for an observation note.  An obsnote is simply a
    free-form note with free-form metadata.
    """
    using_options(tablename='obsnote')

    # Time note was created
    time_create = Field(DateTime)

    # Time note was updated
    time_update = Field(DateTime)

    # Free-form ASCII metadata
    meta = Field(String(500))

    # Free-form memo content
    memo = Field(Unicode(500))

    def __str__(self):
        return '%s: %s' % (str(self.time_create), self.memo)
    def __repr__(self):
        return '<Note %s: %s>' % (str(self.time_create), self.memo)


#END
