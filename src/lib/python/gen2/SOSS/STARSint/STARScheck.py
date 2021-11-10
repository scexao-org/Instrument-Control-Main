#!/usr/bin/env python
#
# STARScheck.py -- Precheck before STARS archiving
#
# Takeshi Inagaki
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Aug 15 14:36:22 HST 2011
#]
#
#
"""
Example usage:
  $ STARScheck.py --stderr [--fix] [--modify] <fitspath> ...
"""
import sys, os
import re
import pyfits

HANDLE_ARCHIVE = 0
HANDLE_REJECT  = 1
HANDLE_WARNING = 2
HANDLE_SILENTREJECT = 4


version = '20110921.0'

class STARScheckError(Exception):
    """Base exception for errors raised in the STARScheck module."""
    pass

class STARScheck(object):

    def __init__(self, logger):
        self.logger = logger

        self.ignorepfx = set([])

        __prop_id = re.compile(r'^o\d{5}$')         # e.g. o11011
        __frame_id= re.compile(r'^\w{3}[AQ]\d{8}$') # e.g. VGWA00000000
        __date_obs=re.compile(r'^2[0-9][0-9][0-9]-(0[1-9]|1[0 1 2])-(0[1-9]|[1 2][0-9]|3[0 1])$') # e.g. 2011-01-01  do not allow 2011-00-00
        __observer = re.compile(r'[a-zA-Z0-9_#]')    # e.g. '#',  '_obs1,obs2,obs3',  ' obs' ,  ' obs1 ',  ' obs1'

        # required keyword 
        self.req_keyword={'PROP-ID' : __prop_id.match,
                          'FRAMEID' : __frame_id.match,
                          'DATE-OBS': __date_obs.match, 
                          'OBSERVER': __observer.search,}

        # checking keyword
        self.chk_keyword={'EQUINOX': {'type': float, 'default': 2000.0},
                          'M2-POS1': {'type': float, 'default': 9999.999},
                          'M2-POS2': {'type': float, 'default': 9999.999},
                          'M2-POS3': {'type': float, 'default': 9999.999},
                          'M2-ANG1': {'type': float, 'default': 99.999},
                          'M2-ANG2': {'type': float, 'default': 99.999},
                          'M2-ANG3': {'type': float, 'default': 99.999}, 
                          'AG-PRB1': {'type': float, 'default': 9999.999}, 
                          'AG-PRB2': {'type': float, 'default': 9999.999},}


    def startIgnorePfx(self, pfx):
        """Provide a FRAMEID prefix that, if matched, will cause the frame
        to be silently rejected.
        """
        self.ignorepfx.add(pfx)
        self.logger.info("Ignored prefixes: %s" % (str(self.ignorepfx)))

    def stopIgnorePfx(self, pfx):
        """Used to undo the effect of startIgnorePfx()
        """
        self.ignorepfx.remove(pfx)
        self.logger.info("Ignored prefixes: %s" % (str(self.ignorepfx)))

    def check(self, fitspath, fitsobj, prihdr, datadict, fix=False):
        """A STARS precheck.  Parameters:
        fitspath: path to the FITS object
        fitsobj: a pyfits object (currently opened 'readonly' or 'update')
        prihdr: the primary HDU's FITS keywords
        datadict: a command bundle having a dictionary-like interface
            for this STARS transaction.
        fix: if True, then attempt to fix the fits file to be STARS
        compliant

        The result is placed in keywords in datadict:
          checkresult: a list of strings describing possible issues with the file
          handling: a code describing how the file should be handled
        """
  
        result = []
        handling = [HANDLE_ARCHIVE]

        def handle(message, handlemethod):
            result.append(message)
            handling[0] |= handlemethod

        def reject(message):
            handle(message, HANDLE_REJECT)

        # required keyword
        for key, check in self.req_keyword.items():
            try:
                val=prihdr[key]
            except Exception as e:
                reject("Keyword error: no key=%s" %key)
                self.logger.error('error: no fitskey=%s. %s' %(key, str(e)))
                continue
            else:
                try:      
                    res = check(val)
                except Exception as e:
                    reject("Fits keyword value format error: key=%s %s" %(key,str(e)))
                    self.logger.error('error: fits keyval format. key=%s %s' %(key, str(e)))
                else:    
                    if not check(val):
                        reject("Fits keyword format error: %s=%s " %(key,str(val))) 
                        self.logger.error("error: fits keyword format error: %s=%s " %(key,str(val)))

        # check keyword value and fix it
        for key, val in self.chk_keyword.items():
            try:
                value=prihdr[key]
                self.logger.debug('checking kwds... %s=%s' %(key, str(value)))
            except Exception as e:
                self.logger.warn('warn: %s' %(e))
                continue
            else:
                if not isinstance(value, val['type']):
                    # note: 
                    #     fitsverify tool -> e.g.  equinox ='2000.0' NG -> 2000.0 OK,  m2-posX = '100.0' OK -> 100.0 OK
                    try:
                        # e.g. float('111.1') -> 111.1 OK,  float('hahah') -> NG
                        conv_val=val['type'](value)
                    except ValueError as e:
                        self.logger.warn('warn: converting type. %s' %e)
                        if fix:
                            self.logger.debug('fixing kwds... %s=%s' %(key, str(val['default'])))
                            # wrong data-type, assign default value
                            prihdr.update(key, val['default'])
                        else:
                            reject('Data-type error: key=%s:%s, val=%s:%s' %(key, val['type'], str(value), type(value)))
                    else:
                        #  update right data-type value. e.g.  equinox ='2000.0' NG -> 2000.0 OK
                        if fix:
                            self.logger.debug('converted value %s=%s' %(key, str(conv_val)))
                            prihdr.update(key, conv_val)

   
        # # Check Subaru proposal id
        # if not kwds.has_key('PROP-ID'):
        #     reject("No PROP-ID keyword found")

        # propid = kwds['PROP-ID'].strip()
        # if not re.match(r'^o\d{5}$', propid):
        #     reject("PROP-ID is not formatted correctly")
        # FRAMEID keyword is not always the same as used in the file prefix
        frameid = datadict['frameid']

        # # Check Subaru frame id
        # if not kwds.has_key('FRAMEID'):
        #     reject("No FRAMEID keyword found")
        # frameid = kwds['FRAMEID'].strip()
        # if not re.match(r'^\w{3}[AQ]\d{8}$', frameid):
        #     reject("FRAMEID is not formatted correctly")

        # FRAMEID keyword is not always the same as used in the file prefix
        frameid = datadict['frameid']

        # Check if we are currently ignoring these frames
        for pfx in self.ignorepfx:
            self.logger.debug("pfx=%s frameid=%s" % (pfx, frameid))
            if frameid.startswith(pfx):
                self.logger.debug("should ignore this frame")
                handle("Frame prefix '%s' is on ignore list" % (pfx),
                       HANDLE_SILENTREJECT)

        # Set result and handling disposition for this transaction
        datadict['checkresult'] = result
        datadict['handling']  = handling[0]

    def check_fits(self, fitspath, fix=False, modify=False):
        """Open and precheck a fits file for STARS correctness.

        If (fix) is True, then attempt to fix errors in the header.
        If (modify) is True then attempt to write the file back out.
        """
        # Extract frame id from file path
        (fitsdir, fitsname) = os.path.split(fitspath)

        # Open the file and extract the FITS keywords.
        fitsobj = None
        try:
            if modify:
                fitsobj = pyfits.open(fitspath, 'update')
            else:
                fitsobj = pyfits.open(fitspath, 'readonly')

        except Exception, e:
            raise STARScheckError("Cannot open FITS file '%s': %s" % (
                    fitsname, str(e)))

        # Read the FITS keywords from the primary HDU
        kwds = {}
        datadict = {}
        try:
            try:
                #if fix:
                # has to fix keyword values before fetching them w/o any exception error.
                fitsobj.verify('silentfix')

                prihdr = fitsobj[0].header

                # Extract primary header 
                kwds = dict(prihdr.items())

                self.check(fitspath, fitsobj, prihdr, datadict, fix=fix)

                # check again to make sure we haven't broken anything
                if fix:
                    fitsobj.verify()
                if modify:
                    fitsobj.flush()
            except Exception, e:
                raise STARScheckError("STARS precheck raised exception for '%s': %s" % (fitsname, str(e)))

        finally:
            fitsobj.close()

        handling = datadict['handling']
        disposition = "Send to STARS"
        if handling & HANDLE_REJECT:
            disposition = "STARS would likely reject: HOLD"
        if handling & HANDLE_SILENTREJECT:
            disposition = "Silently reject"

        # Report results
        result = datadict['checkresult']
        if len(result) > 0:
            self.logger.error("Issues with '%s'" % (fitspath))
            for message in result:
                self.logger.warn(message)
        self.logger.info("Handling: %s" % disposition)


def main(options, args):

    logger = ssdlog.make_logger('STARScheck', options)
    
    checkObj = STARScheck(logger)

    for pfx in options.pfx.split(','):
        pfx = pfx.upper().strip()
        if len(pfx) > 0:
            checkObj.startIgnorePfx(pfx)

    
    for fitspath in args:
        checkObj.check_fits(fitspath, fix=options.fix,
                            modify=options.modify)



if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    import ssdlog
    from optparse import OptionParser

    usage = "usage: %prog [options] <FITS file> [...]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--fix", dest="fix", default=False, action="store_true",
                      help="Fix the FITS file if possible")
    optprs.add_option("--modify", dest="modify", default=False,
                      action="store_true",
                      help="Save modifications back to FITS file")
    optprs.add_option("--pfx", dest="pfx", default='',
                      help="Comma separated list of frame prefixes to ignore")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) <= 0:
        optprs.error("incorrect number of arguments")


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
       
# END

