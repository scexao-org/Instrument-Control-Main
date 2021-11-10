#!/usr/bin/env python
#
# ltcs.py -- Laser Traffic Control System interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri May 22 10:03:40 HST 2009
#]
# Yasu Sakakibara  (yasu@naoj.org)
#
# Description:
# Example implementation of the specification defined in
# "Mauna Kea LTCS URL Interface Specification", ver. 2.0 rel 1.0 (2006.03.16)
#
# Initially also based on inspection of Perl/csh/C/awk code by
# Ryu Ogasawara
#
import sys, os, math, re
import threading, time
import ssdlog
import remoteObjects as ro

logger = None

# -- PYTHON MODULE CONFIGURATION --

# Unless we have our PYTHONPATH set appropriately, we need to tell Python
# where to file the SOSS.status and myproc modules
import SOSS.status
import myproc
import Bunch


class ltcsError(Exception):
    """Class for exceptions raised in this module.
    """
    pass

# -- APPLICATION CONFIGURATION --

version = "20090121.0"

# Template for the HTML output expected by the LTCS system
#
#   <title> Subaru LTCS LTCS-2.1  %(curtime)s  %(curtime_num)d:%(curtime_diff)d</title>
web_template = '''
<html>
<head>
   <title>Subaru LTCS Program</title>

   <meta HTTP-EQUIV="Refresh" CONTENT=%(update)d>
   <meta name="robots" content="noindex,nofollow">

</head>
<body bgcolor="#42426f" text="#FFFFFF" link="black" vlink="navy" alink="red">

<pre>
TIMESTAMP1    = %(timestamp)d
TELESCOPE     = %(telescope)s
LASER_IMPACTED= %(laserimpacted)s 
LASER_STATE   = %(laserstate)s
LOG_DATA      = %(logdata)s
EQUINOX       = %(equinox)-14.1f
RA            = %(ra)-14.4f
DEC           = %(dec)-14.4f
FOV           = %(fov)-14.4f
TIMESTAMP2    = %(timestamp)d
</pre>
<!-- 
   laser impacted reason: %(laseripreason)s
      laser impacted cmd: %(laserimpacted_cmd)s
      laser state reason: %(laserstreason)s
         laser state cmd: %(laserstate_cmd)s
-->
</body>
</html>
'''

# Dictionary of FOV values for Subaru telescope at various foci
# Yutuka Hayano suggests the following values that were determined by
# measurement of Hideki Takami.
# _LTCS URL Interface Specification 2.0_ specifies that the FOV parameter
# should not exceed 1.6667
FOVTEL = {
    'P_OPT':  0.97,
    'P_IR':   0.72,
    'CS':     0.17,
    'NS_OPT': 0.10,
    'NS_IR':  0.15
    }
    
# Dictionary of FOV values for Subaru telescope with various instruments
# These are from the SOSS AgAutoSelect.cfg configuration file.
# Currently these FOV values are not used (FOVTEL values are used instead),
# but this table is used to look up which foci is used with which instrument.
#
#InstrumentFOVradius(Radius:degree)
FOVINS = {
    'SPCAM': ('P_OPT',  0.22433),
    'FMOS':  ('P_IR',   0.22433),
    'FOCAS': ('CS',     0.05),
    'HDS':   ('NS_OPT', 0.002778),
    'OHS':   ('NS_IR',  0.016667),
    'CISCO': ('NS_IR',  0.016667),
    'CAC':   ('CS',     0.011785),
    'MIRTOS':('CS',     0.004222),
    'VTOS':  ('CS',     0.004222),
    'COMICS':('CS',     0.007000),
    'IRCS':  ('NS_IR',  0.016667),
    'CIAO':  ('CS',     0.007000),
    'AO':    ('CS',     0.007000),
    'K3D':   ('CS',     0.016000),
    'MOIRCS':('CS',     0.023570),
    }

# Mapping of needed/default values and their expected types.
# TODO: can this be auto-generated from the template?
web_values = {'update': 10, 'timestamp': 0, 'telescope': 'SUBARU',
              'laserimpacted': 'YES', 'laserimpacted_cmd': 'CALC',
              'laseripreason': 'default',
              'laserstate': 'OFF', 'laserstate_cmd': 'OFF',
              'laserstreason': 'default',
              'equinox': 0.0, 'ra': 0.0, 'dec': 0.0,
              'fov': FOVTEL['P_OPT'], 'logdata': 'ON',
              }

interface = None

###################################################
# PROGRAM
###################################################

class remoteInterface(ro.remoteObjectServer):
    """Simple class to act as a remote method call interface to set
    laserstate or laserimpacted flags.
    """

    def __init__(self, svcname, logger, oldvals, port=None, 
                 usethread=False, secure=False,
                 authDict=None, cert_file=None):

        self.vals = Bunch.threadSafeBunch()
        for var in ('laserstate_cmd', 'laserimpacted_cmd'):
            self.vals[var] = oldvals.get(var, web_values[var])
        
        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=svcname, port=port,
                                       logger=logger,
                                       usethread=usethread,
                                       authDict=authDict, secure=secure,
                                       cert_file=cert_file)
        

    def ro_echo(self, val):
        return val

    def set(self, var, val):
        # This will raise a KeyError if var doesn't exist
        self.logger.info("SETTING %s TO %s" % (var, str(val)))
        x = self.get(var)

        self.vals[var] = val
        return ro.OK

    def get(self, var):
        # This will raise a KeyError if var doesn't exist
        return self.vals[var]


def put_oldvals(statefile, oldvals):
    try:
        out_f = open(statefile, 'w')
        out_f.write(repr(oldvals))
        out_f.close()

    except:
        logger.warn('Could not open statefile for writing oldvals.')


def get_oldvals(statefile, templ, oldvals):
    """Find all the pattern variables in the web template string _templ_
    and set in _kwddict_ the keys for all the variables.
    """
##     regex = re.compile(r'\%\((\w+)\)(.*)$', re.DOTALL)

##     match = True
##     while match:
##         match = regex.search(templ)
##         if match:
##             var = match.group(1)
##             templ = match.group(2)
##             kwddict[var] = ""

    try:
        in_f = open(statefile, 'r')
        oldvals.update(eval(in_f.read()))
        in_f.close()

    except:
        logger.warn('Could not open statefile; using empty oldvals.')


def ra_hrs(ra):
    """Convert ra of the form "21:02:42.941" to decimal hours "21.YYYY" 
    """
    
    ra1 = ra.split(":")

    # Currently appear to just be converting to decimal notation
    # TODO: there is a more efficient calculation using different SOSS
    # status value
    res = float(ra1[0]) + (float(ra1[1])/60) + (float(ra1[2])/3600)
    return res


def dec_deg(dec):
    """Convert dec of the form "+19:48:08.67" to decimal degrees "19.YYYY"
    """

    dec1= dec.split(":")

    # Currently appear to just be converting to decimal notation
    # TODO: there is a more efficient calculation using different SOSS
    # status value
    hrs = float(dec1[0])
    if dec.startswith('-'):
        sign = -1.0
    else:
        sign = 1.0
    res = hrs + (sign * float(dec1[1])/60) + (sign * float(dec1[2])/3600)

    return res


def calc_laserimpact(vals, oldvals, options):
    """Determine the value for the LASERIMPACTED keyword.
    From the spec:
    Observatories should set this flag to YES when ALL of the following are
    true:
        - Dome shutter state is open
        - Dome tracking state is tracking
        - Telescope state is tracking
        - Telescope is guiding
        - Instrument is sensitive to NA589 fluorecence

    Observatories should set this flag to NO when ANY of the following are
    true:
        - Dome shutter state is closed
        - Dome tracking state is parked, slewing
        - Telescope state is parked, slewing
        - Telescope is not guiding
        - Instrument is insensitive to NA589 fluorecence

    Takes a dictionary of keywords and program options and sets values for
    keys 'laserimpacted' and 'laseripreason'.
    """

    # Get some variables we will need to calculate laser impact
    ts = vals['timestamp']
    el = vals['el']
    ra = vals['ra']
    dec = vals['dec']

    # Get previous ta, ra and dec.  If none, then set ts to current ts
    # which will force LASERIMPACTED=YES this round.
    try:
        prev_ts = oldvals['timestamp']
        prev_ra = oldvals['ra']
        prev_dec = oldvals['dec']

    except KeyError, e:
        prev_ts = ts
        prev_ra = 1.0
        prev_dec = 1.0

    # Laser impacted algorithm (currently according to O's script, not as
    # defined in spec):
    #
    # Is dome completely closed?
    if vals.has_key('dome') and vals['dome'] == 'closed':
        # Yes: no laserimpact
        laserip = 'NO'
        reason  = ('dome is closed')

    # Are we still parked at zenith?
    elif abs(el - 90.0) < 0.5:
        # Yes: no laserimpact
        laserip = 'NO'
        reason  = ('el=%4.1f' % el)

    else:
        # If we don't have any old/new data, assume the worst
        if ts == prev_ts:
            laserip = 'YES'
            reason  = 'status not updating'
        else:
            # If moving > 0.01 deg/sec then slewing (say 'NO')
            # otherwise assume we are tracking/guiding/sidereal
            # Uses Pythagorean theorem for calculating distance between
            # (prev_ra, prev_dec) and (ra, dec)
            # TODO: this is from O's script, but I think there are more
            # accurate solutions (e.g. angsep.py)
            #
            #diff = math.sqrt( (prev_ra - ra)**2 + (prev_dec - dec)**2 ) \
            #       / (ts - prev_ts)
            # Update: change to O's script
            diff = math.sqrt( ((prev_ra - ra) * math.cos(prev_dec / 57.29578))**2 \
                              + (prev_dec - dec)**2 ) \
                   / (ts - prev_ts)
            if diff > 0.01:
                laserip = 'NO'
            else:
                laserip = 'YES'
            reason  = ('slewing; diff=%5.4f' % diff)

    vals['laserimpacted'] = laserip
    vals['laseripreason'] = reason


def check_values(vals):

    # For each needed key in the template, check that our dictionary of
    # values has a key with that name and the appropriate type
    for (key, val) in web_values.items():
        if not vals.has_key(key):
            vals[key] = val

        elif not type(vals[key]) == type(val):
            vals[key] = val

# Output the HTML table that defines the LTCS variables
#   template: the HTML template string
#   status: SOSS status module with dict interface
#   oldvals: dict with calculated values from previous invocation
#   options: optparse options object with program options
#
# at end of this routine oldvals is updated with the new values
#
def output(template, status, oldvals, options):

    # Verify consistency of old values
    check_values(oldvals)

    # Initialize new values dict from old values
    vals = {}
    vals.update(oldvals)
    
    # Set the new values
    try:
        # get the current time as timestamp (as per spec)
        ts = int(time.time())
        vals['timestamp'] = ts

        # Default to safe
        vals['laserimpacted'] = 'YES'
        vals['laseripreason'] = 'unknown error'

        # Set floating pt defaults for RA, DEC if no old ones available
        vals['fov'] = FOVTEL['P_OPT']
    
        vals['telescope'] = 'SUBARU'

        # Fetch the needed status from the OCS to analyze
        fetchDict = status.fetch({
                'FITS.SBR.TELESCOP': '#',
                'STATS.EQUINOX': '#',
                'FITS.SBR.RA': '#',
                'FITS.SBR.DEC': '#',
                'CXWS.TSCV.SHUTTER': '#',
                'FITS.SBR.MAINOBCP': '#',
                'TSCS.AZ': '#',
                'TSCS.EL': '#',
                })

        # Acceptable values are OFF, ON and ON-SKY
        # (ON_SKY means our laser is progagating)
        vals['laserstate'] = 'OFF'
        vals['laserstreason'] = "error getting commanded or default value"
        if interface:
            try:
                vals['laserstate_cmd'] = interface.get('laserstate_cmd')
                vals['laserstate'] = vals['laserstate_cmd'].upper()
                vals['laserstreason'] = "Commanded value."
            except Exception, e:
                vals['laserstreason'] = "error: %s" % str(e)
        
        # Do we want other telescopes to log our pointing data.  Leave to
        # ON unless there is a compelling security issue.
        vals['logdata'] = 'ON'

        vals['equinox'] = 2000.0

        #vals['telescope'] = fetchDict['FITS.SBR.TELESCOP'].upper()
        #vals['equinox'] = fetchDict['STATS.EQUINOX']

        # Get RA and DEC & convert appropriately.  Consider changing code
        # to use (TSCS.ALPHA, TSCS.DELTA) or (STATS.RA, STATS.DEC).
        # Formats are different, so conversion rountines would change.
        vals['ra'] = ra_hrs(fetchDict['FITS.SBR.RA'])
        vals['dec'] = dec_deg(fetchDict['FITS.SBR.DEC'])

        # Get dome shutter status
        # The status alias CXWS.TSCV.SHUTTER is a bitfield that contains
        # bits for shutter open and closed:
        # bit    meaning
        # 4      IR side shutter full open
        # 5      IR side shutter full closed
        # 6      Opt side shutter full open
        # 7      Opt side shutter full closed
        #
        shtr_bits = fetchDict['CXWS.TSCV.SHUTTER']
        if (type(shtr_bits) == int) and ((shtr_bits & 0xF0) == 0xA0):
            vals['dome'] = 'closed'
        else:
            vals['dome'] = 'open'
            
        # Get FOV of telescope.  Depends on current instrument and telescope
        # foci.
        if not options.constfov:
            cur_ins = fetchDict['FITS.SBR.MAINOBCP']
            try:
                (foci, fovins) = FOVINS[cur_ins]
                vals['fov'] = FOVTEL[foci]

            except KeyError:
                # If no accurate value available, assume maximum FOV, which is
                # P_OPT
                vals['fov'] = FOVTEL['P_OPT']

        else:
            # Currently hard-coded to 0.25 in O's script, approx value (Cs 15 arcmin)
            #vals['fov'] = 0.25
            # Update: hard-coded to 1.6667 in O's script (SupCam 100 arcmin)
            vals['fov'] = 1.6667

        # Azimuth currently not needed
        #vals['az'] = fetchDict['TSCS.AZ']
        vals['el'] = fetchDict['TSCS.EL']

        vals['laserimpacted'] = 'YES'
        vals['laseripreason'] = "error getting commanded or default value"
        if interface:
            try:
                laserip = interface.get('laserimpacted_cmd').upper()
                vals['laserimpacted_cmd'] = laserip

                if laserip in ('YES', 'NO'):
                    vals['laserimpacted'] = laserip
                    vals['laseripreason'] = "Manual override of calculation."

                elif laserip == 'CALC':
                    # Calculate value of 'laserimpacted' keyword
                    calc_laserimpact(vals, oldvals, options)

                else:
                    vals['laseripreason'] = "Unknown command: %s" % laserip

            except Exception, e:
                vals['laseripreason'] = "error: %s" % str(e)


    except Exception, e:
        # Can't fetch status--assume the worst: that we are peering somewhere
        # they are pointing their laser
        logger.error("Error occured while retrieving status values: '%s'" % str(e))
        vals['laserimpacted'] = 'YES'
        vals['laseripreason'] = 'error: %s' % str(e)

    # Set update value for web page.  Browsers don't handle fast update
    # rates, so limit it to 10 seconds for browser auto-refresh.  LTCS
    # system will of course read at whatever rate it chooses.
    if options.updateperiod < 10.0:
        vals['update'] = 10
    else:
        vals['update'] = int(options.updateperiod)

    # Sanity check on new values
    check_values(vals)
    
    # Interpolate result
    try:
        result = template % vals

    except Exception, e:
        raise ltcsError(str(e))
    
    # Update values for next iteration
    oldvals.update(vals)
    put_oldvals(options.statefile, oldvals)

    return result


def start(options):
    global logger, interface

    # Create top level logger.
    logger = ssdlog.make_logger('ltcs', options)

    ro.init()

    # Use another template if specified
    if not options.template:
        templ = web_template
    else:
        try:
            tmpl_f = open(options.template, 'r')
            templ = tmpl_f.read()
            tmpl_f.close()

        except IOError, e:
            logger.error("Error opening template file '%s': %s\n" % \
                             (options.template, str(e)))
            sys.exit(1)

    # Create status object used for getting OCS status
    if options.statushost:
        status = SOSS.status.cachedStatusObj(options.statushost)
    else:
        status = SOSS.status.g2StatusObj(options.statussvc)

    # Try to read state from previous run.  Mainly need ts, ra and dec.
    oldvals = {}
    get_oldvals(options.statefile, templ, oldvals)

    ev_quit = threading.Event()

    auth = None
    if options.auth:
        auth = options.auth.split(':')
    elif os.environ.has_key('LTCSAUTH'):
        auth = os.environ['LTCSAUTH'].split(':')

    # Special option to use the remoteObjects framework to communicate
    # with a remote daemon that will write the file.
    ro_svc = None
    if options.rohost:
        (rohost, roport) = options.rohost.split(':')
        roport = int(roport)
        ro_svc = ro.remoteObjectClient(rohost, roport, auth=auth,
                                       secure=options.secure)

    if options.svcname:
        tmp = options.svcname.split(':')
        if len(tmp) == 2:
            svcname = tmp[0]
            port = int(tmp[1])
        else:
            svcname = tmp[0]
            port = 8212

        authDict = {}
        if auth:
            authDict[auth[0]] = auth[1]

        logger.info("Starting '%s' service..." % svcname)
        # If --cert is passed, then INSIDE service will be SSL encrypted
        # (part operating inside firewall)
        interface = remoteInterface(svcname, logger, oldvals,
                                    port=options.port,
                                    usethread=True, authDict=authDict,
                                    secure=(options.cert_file != None),
                                    cert_file=options.cert_file)

    try:
        logger.info("Starting LTCS loop...")

        if interface:
            interface.ro_start(wait=True)

        while not ev_quit.isSet():
            # Get time before work
            begintime = time.time()

            try:
                # Get output string to write to file
                result = output(templ, status, oldvals, options)

                # If we are using a remote service, call it here with the
                # buffer contents...
                if ro_svc:
                    buf = ro.binary_encode(result)
                    ro_svc.putFile(buf)

                # Otherwise use the more conventional (and slower) scp copy.
                else:
                    # Use another output file if specified
                    if not options.outputfile:
                        web_f = sys.stdout
                    else:
                        try:
                            web_f = open(options.outputfile, 'w')

                        except IOError, e:
                            raise ltcsError("Error opening output file '%s': %s\n" % \
                                            (options.outputfile, str(e)))

                    # Output HTML to the file and close it.
                    web_f.write(result)
                    web_f.flush()

                    if options.outputfile:
                        web_f.close()

                    # If we are asked to scp the file to another host, do so.
                    # Fail gracefully.
                    if options.scpdst:
                        try:
                            res = os.system("scp %s %s" % \
                                            (options.outputfile, options.scpdst))
                        except OSError, e:
                            raise ltcsError("Error scp-ing file: %s\n" % \
                                            (str(e)))
                
            except KeyboardInterrupt, e:
                raise e
                
            except Exception, e:
                # If there is an error, then log it and continue.
                logger.error(str(e))

            # Get time after work
            endtime = time.time()

            # Now sleep for just enough until the update period
            sleepval = options.updateperiod - (endtime - begintime)

            if sleepval > 0:
                ev_quit.wait(options.updateperiod)
            else:
                logger.warn("Can't keep up with update period: %f" % \
                                     (options.updateperiod))
                

    except KeyboardInterrupt:
        if interface:
            interface.ro_stop(wait=False)

    logger.info("Terminating LTCS.")
    sys.exit(0)
    

def status(options):
    if not options.pidfile:
        print "Please specify a --pidfile"
        sys.exit(1)
        
    print "Looking for LTCS process..."
    try:
        child = myproc.getproc(pidfile=options.pidfile)
        print child.status()

    except myproc.myprocError, e:
        print "Error getting PID for LTCS process; please check manually"

    sys.exit(0)


def stop(options):
    if not options.pidfile:
        print "Please specify a --pidfile"
        sys.exit(1)
        
    print "Looking for LTCS process..."
    try:
        child = myproc.getproc(pidfile=options.pidfile)
        if child.status != 'exited':
            print "Trying to stop LTCS process..."
            child.kill()
            sys.exit(0)
        else:
            print "No LTCS process found."
            sys.exit(1)
    except myproc.myprocError, e:
        print "Error getting PID for LTCS process; please check manually"

    sys.exit(0)
    

def main(options, args):

    cmd = args[0]
    
    # Stop daemon?
    if cmd == 'stop':
        return stop(options)

    # Check status?
    elif cmd == 'status':
        return status(options)

    # Check status?
    elif cmd == 'start':
        if options.detach:
            try:
                null_f = open('/dev/null', 'w')

            except IOError, e:
                sys.stderr.write("Could not open /dev/null: %s" % (str(e)))
                sys.exit(1)

            print "Detaching from this process..."
            child = myproc.myproc(start, args=[options],
                                  pidfile=options.pidfile, detach=True,
                                  stdout=null_f, stderr=null_f)

            null_f.close()
            sys.exit(0)

        return start(options)

    else:
        print "I don't know what '%s' means; invoke with --help to see usage" % (
            cmd)
        sys.exit(1)


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] start|stop|status"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))

    optprs.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    optprs.add_option("--cert", dest="cert_file",
                      help="Path to key/certificate file")
    optprs.add_option("--constfov", dest="constfov", action="store_true",
                      default=False,
                      help="Use a constant FOV instead of calculating it from the current telescope configuration")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Run process as a detached daemon")
    optprs.add_option("--host", dest="statushost",
                      help="Use HOST to pull status", metavar="HOST")
    optprs.add_option("-o", "--output", dest="outputfile", metavar="FILE",
                      help="Write html output to FILE")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("--port", dest="port", type="int", default=8212,
                      help="Register for web service using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--state", dest="statefile", metavar="FILE",
                      default="/data/LTCS/state/ltcs.state",
                      help="Maintain state in to FILE")
    optprs.add_option("--scpdst", dest="scpdst", 
                      help="scp the output file to DST")
    optprs.add_option("--secure", dest="secure", action="store_true",
                      default=False,
                      help="Use SSL encryption")
    optprs.add_option("--svcname", dest="svcname",
                      default=None,
                      help="Register using service NAME", metavar="NAME")
    optprs.add_option("--statussvc", dest="statussvc",
                      default="status",
                      help="Use service NAME to pull status", metavar="NAME")
    optprs.add_option("--rohost", dest="rohost",
                      default=None,
                      help="Connect to host:port")
    optprs.add_option("-t", "--template", dest="template", metavar="FILE",
                      help="Use the template in FILE for writing output")
    optprs.add_option("-u", "--update", dest="updateperiod", metavar="SEC",
                      type='float', default=10.0,
                      help="Set update cycle to SEC seconds")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 1:
        optprs.error("incorrect number of arguments")

    elif not (args[0] in ('start', 'stop', 'status')):
        optprs.error("unknown command: '%s'" % args[0])

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
