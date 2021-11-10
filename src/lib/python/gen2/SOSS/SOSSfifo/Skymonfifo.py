#!/usr/bin/env python

import sys, time

import SOSSfifo


_FIFO_KIND = {
    'FILENAME': "FILENAME  ",
    'WEBEND':   "WEBEND    ",
    'FITSEND':  "FITSEND   ",
    'NORMAL':   "NORMAL    ",
    'ERROR':    "ERROR     ",
    }

class SkymonfifoMsgError(SOSSfifo.SOSSfifoMsgError):
    pass

class SkymonfifoMsg(SOSSfifo.SOSSfifoMsg):
    """
    DESCRIPTION
    Field        Pos  Len  Description
    KIND           0   10  10 byte ASCII command (e.g. "FILENAME")
    FNAME         10   90  90 byte file path
                       --
                      100

    """

    def __init__(self):
    
        # TODO: FIFO messages should be initialized to 100 bytes of NULLs ??
        # Setting a field overrides the nulls.
        
        # allots 'kind' and 'reserved'
        super(SkymonfifoMsg, self).__init__()

        # Additional fields
        self.fname = ''


    def new_message(self, **kwdargs):
        """Same as 'set'. """

        self.set(**kwdargs)


    def message2str(self):
        
        msgstr = "%-10.10s%-90.90s" % (
            self.kind,
            self.fname )

        self.msgCheck(msgstr)

        return msgstr
                                  

def error(msg):
    sys.stderr.write(msg + '\n')

    
def main(options, args):

    # Make sure there is at least 1 argument
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    # Valididate fifo command
    try:
        kind = _FIFO_KIND[options.kind.upper()]

    except KeyError, e:
        sys.stderr.write("Not a valid Skymon fifo command: '%s'" % options.kind)
        sys.exit(1)

    fitspath = args.pop(0)
    msg = SkymonfifoMsg()
    msg.set(kind=kind, fname=fitspath)

    sys.stderr.write("Outputting fifo string for '%s'...\n" % options.kind)
    sys.stdout.write(str(msg))
    if options.newline:
        sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] <FITS file> ..."
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("-n", "--newline", dest="newline", action="store_true",
                      default=False,
                      help="Output a newline between fifo records")
    parser.add_option("-k", "--kind", dest="kind", default='FILENAME',
                      help="Specify the kind of fifo message.")

    (options, args) = parser.parse_args(sys.argv[1:])
    
    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)
    
#END
