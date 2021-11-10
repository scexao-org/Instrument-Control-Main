#
# SCEXAO.py -- SCEXAO personality for g2cam instrument interface
#
#
"""
This file implements a SCEXAO instrument interface for Subaru Gen2.

To install the g2cam package necessary to use this do:

    $ pip install git+https://github.com/naojsoft/g2cam.git

You can run it using Python 2.7 or Python 3.5 or later.  We recommend
Python 3!

Put this file in a subdirectory named "cams" and run it from just outside
the subdirectory like this:

    $ g2cam --cam=SCEXAO --gen2host=<gen2host> --loglevel=20 --stderr

Substitute the name of the Gen2 host (summit or one of the simulators)
for <gen2host>.  You may need to specify the FQDN of the Gen2 host.

After starting this program, you can execute commands from Gen2 observation
scripts like:

   exec SCEXAO archive_fits frame_no=&get_f_no[SCEXAO A] path=/path/to/file.fits

Looking at the methods below the comment "SCEXAO INSTRUMENT COMMANDS"
you can get a sense of how to implement new commands.
"""
from __future__ import print_function
import sys, os, time
import re

# gen2 base imports
from g2base import Bunch, Task

# g2cam imports
from g2cam.Instrument import BASECAM, CamError, CamCommandError
from g2cam.util import common_task


class SCEXAO_Error(CamCommandError):
    pass

class SCEXAO(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(SCEXAO, self).__init__()

        self.logger = logger
        self.env = env
        self.ev_quit = ev_quit
        self.insname = 'SCEXAO'

        # Holds our link to OCS delegate object
        self.ocs = None

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()

        # Interval between status packets (secs)
        self.param.status_interval = 60.0

        # status we are interested in
        self.s_aliases = ['FITS.SBR.RA', 'FITS.SBR.DEC', 'FITS.SBR.EQUINOX',
                          'FITS.SBR.HA', 'FITS.SBR.AIRMASS',
                          'TSCS.AZ', 'TSCS.EL',
                          # add more here if you like
                          ]

        #self.framefile = "/tmp/frames.txt"

    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.
        '''
        super(SCEXAO, self).initialize(ocsint)
        self.logger.info('***** INITIALIZE CALLED *****')
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Get instrument configuration info
        self.obcpnum = self.ocs.get_obcpnum()
        self.insconfig = self.ocs.get_INSconfig()

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool

        # For task inheritance:
        self.tag = 'scexao'
        self.shares = ['logger', 'ev_quit', 'threadPool']

        # Get our 3 letter instrument code and full instrument name
        self.inscode = self.insconfig.getCodeByNumber(self.obcpnum)
        self.insname = self.insconfig.getNameByNumber(self.obcpnum)
        print(self.inscode,self.insname)

        # Figure out our status table name.
        tblName1 = ('%3.3sS%04.4d' % (self.inscode, 1))

        self.stattbl1 = self.ocs.addStatusTable(tblName1,
                                                ['status', 'mode', 'count',
                                                 'time'])

        # Add other tables here if you have more than one table...

        # Establish initial status values
        self.stattbl1.setvals(status='ALIVE', mode='AVAILABLE', count=0,
                              time=time.time())

        # Handles to periodic tasks
        self.status_task = None


    def start(self, wait=True):
        super(SCEXAO, self).start(wait=wait)

        self.logger.info('SCEXAO ocs interface started.')

        # Start auto-generation of status task
        t = common_task.IntervalTask(self.putstatus,
                                     self.param.status_interval)
        self.status_task = t
        t.init_and_start(self)


    def stop(self, wait=True):
        super(SCEXAO, self).stop(wait=wait)

        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        self.logger.info("SCEXAO ocs interface stopped.")


    #######################################
    # INTERNAL METHODS
    #######################################

    def dispatchCommand(self, tag, cmdName, args, kwdargs):
        self.logger.debug("tag=%s cmdName=%s args=%s kwdargs=%s" % (
            tag, cmdName, str(args), str(kwdargs)))

        params = {}
        params.update(kwdargs)
        params['tag'] = tag

        try:
            # Try to look up the named method
            method = getattr(self, cmdName)

        except AttributeError as e:
            result = "ERROR: No such method in subsystem: %s" % (cmdName)
            self.logger.error(result)
            raise CamCommandError(result)

        return method(*args, **params)

    #######################################
    # SCEXAO INSTRUMENT COMMANDS
    #######################################

    def sleep(self, sleep_time=0, tag=None):
        """Useful command just to test whether instrument command
        interface is working.
        """
        itime = float(sleep_time)

        self.logger.info("Sleeping for %f sec..." % itime)
        time.sleep(itime)


    def putstatus(self, target="ALL", tag=None):
        """Forced export of our status.
        Useful command to test whether instrument status export is working.
        """
        # Bump our status send count and time
        self.stattbl1.count += 1
        self.stattbl1.time = time.time()

        self.ocs.exportStatus()


    def getstatus(self, target="ALL", tag=None):
        """Forced import of our status using the normal status interface.
        Useful command to test whether instrument status request is working.
        """
        # use this call in any command where you need to fetch the current
        # values of the status aliases
        d = self.ocs.requestOCSstatusList2Dict(self.s_aliases)

        self.logger.info("Status returned: %s" % (str(d)))


    def archive_fits(self, frame_no=None, path=None, tag=None):
        """Archive a local file to Gen2.

        Parameters
        ----------
        frame_no: str
            the frame number allocated for this frame

        path: str
            the local path on the SCEXAO computer for the file
        """

        if frame_no is None:
            raise SCEXAO_Error("Missing frame number!")

        # Check frame_no
        match = re.match('^(\w{3})(\w)(\d{8})$', frame_no)
        if not match:
            raise SCEXAO_Error("frame_no: '%s' doesn't match expected format" % (frame_no))

        if path is None:
            raise SCEXAO_Error("Missing path!")

        if not os.path.exists(path):
            raise SCEXAO_Error("Path (%s) does not refer to a file!" % (path))

        # determine size of file for error checking
        st = os.stat(path)

        # Tell Gen2 about the file, and it will copy it and archive it
        framelist = [(frame_no, path, st.st_size)]
        self.logger.info("Submitting framelist '%s'" % str(framelist))
        self.ocs.archive_framelist(framelist)


    def get_frames(self, frtype='A', num=1, tag=None):
        # obtain Gen2 frames
        framelist = self.ocs.getFrames(num, frtype)

        # write frame list to file
        with open("/tmp/frames_%s.txt" % (frtype,), 'w') as out_f:
            out_f.write('\n'.join(framelist))



# END
