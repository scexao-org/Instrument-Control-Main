#!/usr/bin/env python

#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu May 23 13:57:01 HST 2013
#]

"""
  TSCTrackFile.py - Functions to write tracking coordinate information
                    to a file in a form suitable for the Subaru TSC
                    and also to copy such a file to the TSC
                    computer. The intent of this code is to make it
                    easy to write a file with non-sidereal tracking
                    coordinates so that the Subaru telescope can track
                    non-sidereal targets. Note that the TSC output file
                    is limited to 6000 data points (Subaru TSC restriction).

"""

import os, sys, datetime
import remoteObjects as ro
import ssdlog
import astro.radec as radec
import myproc

sshKeyFilename = '~/.ssh/id_kansoku_g2s4_rsa'
tscPath = 'naoj@tsc:/JNLT/DATA/TSC/USER/MTDR/EXEC/UG8'
#tscPath = 'rkackley@fldmon:/home/rkackley'

maxNpt = 6000

class NPTOverflowError(Exception):
    pass

def _pmFmt(pm):
    return '%+08.4f' % pm

def _parallaxFmt(parallax):
    return ' %+06.3f' % parallax

# Header for Subaru TSC tracking file
def _writeHeader(file, trackinfo, npt):
    file.write('#%s\n' % trackinfo['description']) # Comment line
    file.write(_pmFmt(trackinfo['pm_ra']))          # RA proper motion (arcsec/yr)
    file.write(' %s' % _pmFmt(trackinfo['pm_dec'])) # Dec proper motion (arcsec/yr)
    file.write(' ON%')                              # E-term
    file.write(_parallaxFmt(trackinfo['parallax'])) # Annual parallax (arcsec)
    file.write('\n')
    file.write(trackinfo['timescale'])              # Time scale (UTC/TDT)
    file.write(' %s' % trackinfo['coord_descr'])    # Coordinate description
    file.write('\n')
    file.write('ABS\n')                             # ABS/REL
    file.write('TSC\n')                             # Flag for Az drive direction (+/-/TSC)
    file.write('%d\n' % npt)                        # Number of data points

# Date format for Subaru TSC tracking file
def _dateTscFmt(date):
    return '.'.join([date.strftime('%Y%m%d%H%M%S'), '%03d'%(int(date.microsecond / 1000))])

# Returns RA as a string in the correct format for Subaru TSC tracking
# file
def _raTscFmt(raDeg):
    return ' %s' % radec.raDegToString(raDeg)
    
# Returns Dec as a string in the correct format for Subaru TSC
# tracking file
def _decTscFmt(decDeg):
    return ' %s' % radec.decDegToString(decDeg)

# Returns Earth-to-body distance as a string in the correct format for
# Subaru TSC tracking file
def _distTscFmt(dist):
    return ' %13.9f' % dist
    
# Returns equinox as a string in the correct format for Subaru TSC
# tracking file
def _eqnxTscFmt(eqnx):
    return ' %9.4f' % eqnx

# Given the tracking coordinate info, write the time history to the
# specified file
def _writeTimeHistory(file, trackInfo):
    for data in trackInfo['timeHistory']:
        file.write(_dateTscFmt(data[0]))
        file.write(_raTscFmt(data[1]))
        file.write(_decTscFmt(data[2]))
        file.write(_distTscFmt(data[3]))
        file.write(_eqnxTscFmt(trackInfo['equinox']))
        file.write('\n')

# Given the tracking coordinate info, write the required header and
# time history to the specified output file
def writeTSCTrackOutput(outfile, trackInfo, logger):
    npt = len(trackInfo['timeHistory'])
    if npt > maxNpt:
        raise NPTOverflowError('Number of output points exceeds max allowed: %d > %d' % (npt, maxNpt))
    _writeHeader(outfile, trackInfo, npt)
    _writeTimeHistory(outfile, trackInfo)
  
def writeTSCTrackFile(filename, trackInfo, logger=None):
    """
    Write time-history suitable for Subaru TSC.

    Args:
        filename:  output filename
        trackInfo: tracking coordinate info (as a python dict)
                   containing the following information:
                   - target description (in the 'description' key)
                   - RA proper motion (arcsec/yr) (in the 'pm_ra' key)
                   - Dec proper motion (arcsec/yr) (in the 'pm_dec' key)
                   - annual parallax (arcsec) (in the 'parallax' key)
                   - time scale (UTC or TDT) (in the 'timescale' key)
                   - coordinate description (in the 'coord_descr' key)
                   - equinox (in the 'equinox' key)
                   - time history of tracking coordinates and
                     target distance (in the 'timeHistory' key)
        logger:     An ssdlog object

        The time history is an array of tuples with each tuple containing:
          - UTC date/time (python datetime object)
          - RA (degrees)
          - Dec (degrees)
          - target distance (AU)

    Returns:
        Nothing

    Raises:
        Nothing
    """
    if logger == None:
        logger = ro.nullLogger()
    # Write header and time-history suitable for Subaru TSC to
    # specified file
    with open(filename, 'w') as outfile:
        writeTSCTrackOutput(outfile, trackInfo, logger)
    logger.info('Output written to %s' % filename)

def copyToTSC(filepath, tscFilename='nstrack.dat', logger=None):
    # Use scp to copy the file with the TSC-format coordinates to the
    # TSC computer.
    if logger == None:
        logger = ro.nullLogger()
    tscFullPath = os.path.join(tscPath, tscFilename)
    cmdstr = ' '.join(['scp', '-i %s' % sshKeyFilename, filepath, tscFullPath])
    logger.info('cmdstr is %s' % cmdstr)
    try:
        proc = myproc.myproc(cmdstr)

        # Wait for the scp process to finish
        proc.wait(10)
        # If the exit code is 0, report that the copy was
        # successful. Otherwise, raise an Exception
        if proc.getexitcode() == 0:
            if logger:
                logger.info('%s copied to %s' % (filepath, tscFullPath))
        else:
            raise Exception('Unable to copy %s to TSC computer %s: %s' % (filepath, tscFullPath, str(proc.error())))
    except Exception as e:
        raise Exception(str(e))

    return tscFullPath

def main(options, args):
    # Create top level logger.
    logger = ssdlog.make_logger('TSCTrackFile', options)

    with open(options.infile, 'r') as f:
        infile = f.read()

if __name__=='__main__':

    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-f", dest="infile", default=None,
                      help="Input file")
    optprs.add_option("-o", dest="outfile", default='sbrtsc.dat',
                      help="Output file")

    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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
