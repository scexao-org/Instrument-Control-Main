#!/usr/bin/env python

#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Apr 30 10:05:19 HST 2013
#]

"""
  jplHorizonsIF.py - Provides an interface to the JPL Horizons website
                     from which you can generate non-sidereal tracking
                     coordinates and write output to a file in a
                     format compatible with the Subaru TSC. You can
                     either run this script from the command-line or
                     use the JPLHorizonsEphem class contained herein to
                     generate the information required to create a
                     tracking coordinate file.

  Command-line options:

  Input options (supply either of the following):
    -f <input file> (output from JPL Horizons)
    -t, --target=<target>     (Solar system major body, planetary moon, comet, or asteroid name)

  Start/end/increment for output:
    --start=<date/time> (start time of output, defaults to current time, UTC)
    --end=<date/time>   (end time of output, UTC)
    --incr=<value>      (increment between output points, default is 30 minutes)
    --duration=<value>  (duration of observation - can be used instead of
                         specifying end time - default is 1 hour)

  Output options:
    -o, --out=<filename>   (output filename (Subaru TSC-format output)
                        - default is output to screen only)

    --jplOut=<filename> (JPL Horizons output - default is to output
                         only Subaru TSC-format output, not JPL Horizons)

  Command-line example:
     ./jplHorizonsIF.py -t Jupiter

  Example of using the JPLHorizonsEphem class:

     import astro.jplHorizonsIF as jplHorizonsIF
     import astro.TSCTrackFile as TSCTrackFile
     jplHorizonsOutput = jplHorizonsIF.jplHorizonsGetEphem('20130301', '20130302', 60, targetName='Jupiter')
     jplHorizonsEphem = jplHorizonsIF.JPLHorizonsEphem(jplHorizonsOutput)
     TSCTrackFile.writeTSCTrackFile('output.tsc', jplHorizonsEphem.trackInfo)

"""

import os, sys, re, datetime, math
import urllib
import remoteObjects as ro
import ssdlog
import astro.radec as radec
import astro.TSCTrackFile as TSCTrackFile
import astro.jplObjectDBSearch as jplObjectDBSearch

# We need slalib only to convert Julian Dates to Calendar Dates. If we
# can't find slalib, set a flag to indicate that we can't parse Julian
# Dates.
try:
    from pyslalib import slalib
    jdOk = True
except ImportError:
    jdOk = False

jplHorizonsURL = 'http://ssd.jpl.nasa.gov/horizons.cgi'

jplHorizonsDefaultSettings = {'ephemerisType': {'table_type': 'OBSERVER', 'set_table_type': 'Use Selection Above'},
                              'tableSettings': {'q_list': '1,20',
                                                'time_fmt':'CAL',
                                                'time_digits': 'FRACSEC',
                                                'ang_format': 'HMS',
                                                'range_units': 'AU',
                                                'suppress_range_rate': 'YES',
                                                'extra_prec': 'YES',
                                                'ref_system':'J2000',
                                                'csv_format': 'NO',
                                                'obj_data':'YES',
                                                'set_table':'Use Settings Above',
                                                'set_table_settings':'1'},
                              'outputType': {'display':'TEXT', 'set_display':'Use Selection Above'},
                              'date': {'start_time': '2012-01-01 00:00',
                                       'stop_time': '2012-01-01 00:10',
                                       'step_size': '1',
                                       'interval_mode': 'm',
                                       'set_time_span': 'Use Specified Times'},
                              'target': {'body': 'MB:499',
                                         'select_body': 'Select Indicated Body'}}

defaultDurationDays = 0
defaultDurationHours = 1

class MultipleTargetMatchError(Exception):
    pass

class HorizonsParseError(Exception):
    pass

class NoSlalibError(Exception):
    pass

class DateTimeFormatError(Exception):
    pass

class MissingInputError(Exception):
    pass

class JPLHorizonsEphem(object):
    def __init__(self, jplHorizonsOutput, logger=ro.nullLogger()):
        self.jplHorizonsOutput = jplHorizonsOutput
        self.logger = logger
        # The parsing results will be stored in the trackInfo data
        # structure.
        self.trackInfo = {'pm_ra': 0, 'pm_dec': 0, 'parallax': 0, 'timescale': 'UTC', 'coord_descr': 'Geocentric Equatorial Mean Polar Geocentric'}
        self.parseJPLHorizonsOutput()

    def parseJPLHorizonsOutput(self):

        # The JPL Horizons output might be supplied to us as either a
        # plain text file or the information might be embedded in an
        # HTML page. Either way, split the output into separate lines.
        lines = self.jplHorizonsOutput.split('\n')

        # The ephemeris data is prefaced with the string "$$SOE" and
        # ends with the string "$$EOE". Locate the lines with those
        # strings. If we can't find those strings, something is wrong
        # with the input and there isn't much we can do except raise
        # an exception.
        soeLineNum = self.locateLine(lines, 0, re.compile('^\$\$SOE'))
        if not soeLineNum:
            raise HorizonsParseError('$$SOE not found in JPL Horizons data. Can not parse input.')
        eoeLineNum = self.locateLine(lines, soeLineNum, re.compile('^\$\$EOE'))
        if not eoeLineNum:
            raise HorizonsParseError('$$EOE not found in JPL Horizons data. Can not parse input.')

        # From the locations of the "$$SOE" and "$$EOE" lines, we can
        # deduce the lines with the preface (information preceeding
        # the ephemeris data), the header (tells us what is in each
        # column of the ephemeris data), and the appendix (information
        # following the ephemeris data).
        preface = lines[:soeLineNum-3]
        headerLine = lines[soeLineNum-2]
        ephemData = lines[soeLineNum+1:eoeLineNum]
        appendix = lines[eoeLineNum+2:]

        # Get the target description from the preface
        self.trackInfo['description'] = self.getTargetDescr(preface)

        # We have to look at the column headers to make sure we have
        # what we need in the ephemeris data.
        columns = {}

        # A line in the preface will tell us if the ephemeris data is
        # supplied as comma-separated values. If that line is not
        # found, then the ephemeris data is space-separated.
        lineNum = self.locateLine(preface, 0, re.compile('^Table format\s*: Comma Separated Values'))
        if lineNum:
            columns['sep'] = ','
        else:
            columns['sep'] = None

        # Parse the headers to figure out what we were supplied in the
        # ephemeris data.
        self.parseJPLHorizonsHeaders(headerLine, preface, appendix, columns)

        # For each line in the ephemeris data, extract the time,
        # RA/Dec, and target distance and add a tuple of those
        # quantities to the trackInfo data structure.
        self.trackInfo['timeHistory'] = []
        for line in ephemData:
            raDeg, decDeg = self.getRaDecDeg(line, columns)
            date = self.getDate(line, columns)
            delta = self.getDelta(line, columns)
            self.trackInfo['timeHistory'].append((date, raDeg, decDeg, delta))

    def parseJPLHorizonsHeaders(self, headerLine, preface, appendix, columns):

        # Split the header line into the column headings
        headers = headerLine.split(columns['sep'])

        # Look through the column headers and make sure we find all
        # the ones we need (date, RA/Dec, and delta). Also, figure out
        # where the columns start and end and what kind of format that
        # columns are in (e.g., is date HH:MM or HH:MM:SS, etc.).
        i = 0
        for header in headers:
            header = header.strip()
            headers[i] = header
            if re.match('^Date__', header):
                dateHeader = header
                dateType, dateFmt = self.getDateType(preface, dateHeader)
                dateHeaderStart = headerLine.find(dateHeader)
                dateHeaderEnd = dateHeaderStart + len(dateHeader)
                columns['Date'] = {'Name': 'Date', 'type': dateType, 'format': dateFmt, 'start': dateHeaderStart, 'end': dateHeaderEnd, 'num': i}

            if re.match('^R.A._\S*_DEC$', header) or re.match('^R.A._\S*_DEC.$', header) :
                raDecHeader = header
                raDecType = self.getRADecType(preface)
                self.trackInfo['equinox'] = self.getEquinox(raDecHeader)
                raDecHeaderStart = headerLine.find(raDecHeader)
                raDecHeaderEnd = raDecHeaderStart + len(raDecHeader)
                columns['radec'] = {'Name': 'RA/Dec', 'type': raDecType, 'start': raDecHeaderStart, 'end': raDecHeaderEnd}
            if re.match('^R.A._\(\S*\)$', header):
                raHeader = header
                raDecType = self.getRADecType(preface)
                self.trackInfo['equinox'] = self.getEquinox(raHeader)
                columns['ra'] = {'Name': 'RA', 'type': raDecType, 'num': i}
            if re.match('^DEC_\(\S*\)$', header):
                decHeader = header
                raDecType = self.getRADecType(preface)
                self.trackInfo['equinox'] = self.getEquinox(decHeader)
                columns['dec'] = {'Name': 'Dec', 'type': raDecType, 'num': i}
            if re.match('^delta', header):
                deltaHeader = header
                deltaUnits = self.getDeltaUnits(appendix)
                if deltaUnits == 'KM':
                    deltaConvFactor = self.getDeltaConvFactor(preface)
                else:
                    deltaConvFactor = 1.0
                deltaHeaderStart = headerLine.find(deltaHeader)
                deltaHeaderEnd = deltaHeaderStart + len(deltaHeader)
                deltaHeaderStart = deltaHeaderEnd - 16
                columns['delta'] = {'Name': 'delta', 'units': deltaUnits, 'convFactor': deltaConvFactor, 'start': deltaHeaderStart, 'end': deltaHeaderEnd, 'num': i}
            i += 1

    def getDateType(self, preface, dateHeader):
        lineNum = self.locateLine(preface, 0, re.compile('^Time format\s*:'))
        tokens = preface[lineNum].split()
        dateType = tokens[-1]
        if dateType == 'BOTH':
            dateType = 'JD'

        if dateType == 'JD' and not jdOk:
            raise NoSlalibError('Julian dates require slalib, but slalib is not available')

        if dateHeader == 'Date__(UT)__HR:MN':
            dateFmt = '%Y-%b-%d %H:%M'
        elif dateHeader == 'Date__(UT)__HR:MN:SS' or \
                 dateHeader == 'Date__(UT)__HR:MN:SC.fff':
            dateFmt = '%Y-%b-%d %H:%M:%S'
        else:
            dateFmt = None        
        return dateType, dateFmt

    def getRADecType(self, preface):
        lineNum = self.locateLine(preface, 0, re.compile('^RA format\s*:'))
        tokens = preface[lineNum].split()
        radecType = tokens[-1]
        return radecType

    def getEquinox(self, raDecHeader):
        if 'J2000' in raDecHeader:
            return 2000.0
        elif 'B1950' in raDecHeader:
            return 1950.0
        else:
            return None

    def getDeltaUnits(self, appendix):
        lineNum = self.locateLine(appendix, 0, re.compile('delta\s+\w*\s+='))
        unitsString = 'Units: '
        lineNum = self.locateLine(appendix, lineNum, re.compile(unitsString))
        unitsStringStart = appendix[lineNum].find(unitsString)
        unitsStart = unitsStringStart + len(unitsString)
        units = appendix[lineNum][unitsStart:unitsStart+2]
        return units

    def getDeltaConvFactor(self, preface):
        lineNum = self.locateLine(preface, 0, re.compile('^Units conversion:'))
        convStringStart = preface[lineNum].find('1 AU=')
        convStringEnd = preface[lineNum].find(' km')
        dum1, dum2, deltaConvFactor = preface[lineNum][convStringStart:convStringEnd].split()
        return 1.0/float(deltaConvFactor)

    def getTargetDescr(self, preface):
        lineNum = self.locateLine(preface, 0, re.compile('^Target body name: '))
        targetStringStart = preface[lineNum].find(':') + 2
        targetDescr = preface[lineNum][targetStringStart:]
        return targetDescr

    # Get the date values from the JPL Horizons output and return it
    # as a python datetime object
    def getDate(self, line, columns):
        if columns['sep'] == ',':
            fields = line.split(columns['sep'])
            dateStr = fields[columns['Date']['num']].strip()
        else:
            dateStr = line[columns['Date']['start']:columns['Date']['end']]
        if columns['Date']['type'] == 'CAL':
            dateFmt = columns['Date']['format']
            if '.' in dateStr:
                dateTimeStr, msecStr = dateStr.split('.')
                msec = int(msecStr)
            else:
                dateTimeStr = dateStr
                msec = 0
        elif columns['Date']['type'] == 'JD':
            # The subtraction is because sla_djcl wants an MJD
            jd = float(dateStr)
            yy, mm, dd, fracDay, j = slalib.sla_djcl(jd - 2400000.5)
            sign, hmsf = slalib.sla_dd2tf(3, fracDay)
            dateStr = '-'.join([str(yy), '%02d' % mm, '%02d' % dd])
            timeStr = ':'.join(['%02d' % hmsf[0], '%02d' % hmsf[1], '%02d' % hmsf[2]])
            dateTimeStr = ' '.join([dateStr, timeStr])
            dateFmt = '%Y-%m-%d %H:%M:%S'
            msec = int(hmsf[3])

        date = datetime.datetime.strptime(dateTimeStr, dateFmt) + datetime.timedelta(milliseconds = msec)
        return date

    # Get the RA/Dec values from the JPL Horizons output and return
    # them as decimal degrees
    def getRaDecDeg(self, line, columns):
        if columns['sep'] == ',':
            fields = line.split(columns['sep'])
            raStr = fields[columns['ra']['num']].strip()
            decStr = fields[columns['dec']['num']].strip()
            if columns['ra']['type'] == 'HMS':
                raDeg = radec.hmsStrToDeg(raStr.replace(' ',':'))
                decDeg = radec.dmsStrToDeg(decStr.replace(' ',':'))
            elif columns['ra']['type'] == 'DEG':
                raDeg = float(raStr)
                decDeg = float(decStr)
        else:
            raDecStr = line[columns['radec']['start']:columns['radec']['end']]
            if columns['radec']['type'] == 'HMS':
                raHr, raMin, raSec, decDeg, decMin, decSec = raDecStr.split()
                raDeg = radec.hmsStrToDeg(':'.join([raHr, raMin, raSec]))
                decDeg = radec.dmsStrToDeg(':'.join([decDeg, decMin, decSec]))
            elif columns['radec']['type'] == 'DEG':
                raDeg, decDeg = raDecStr.split()
                raDeg = float(raDeg)
                decDeg = float(decDeg)
            return raDeg, decDeg

    # Get the target distance from the JPL Horizons output, convert it to AU,
    # and return the value
    def getDelta(self, line, columns):
        if columns['sep'] == ',':
            fields = line.split(columns['sep'])
            deltaStr = fields[columns['delta']['num']].strip()
        else:
            deltaStr = line[columns['delta']['start']:columns['delta']['end']]
        delta = float(deltaStr) * columns['delta']['convFactor']
        return delta

    def locateLine(self, lines, startNum, regexp):
        i = startNum
        found = False
        lineNum = None
        while not found and i < len(lines):
            if regexp.search(lines[i]):
                found = True
                lineNum = i
            else:
                i += 1
        return lineNum

    def getInitialRaDec(self):
        initialRaDeg = self.trackInfo['timeHistory'][0][1]
        initialDecDeg = self.trackInfo['timeHistory'][0][2]
        return radec.raDegToString(initialRaDeg, format='%02d:%02d:%06.3f'), radec.decDegToString(initialDecDeg, format='%s%02d:%02d:%05.2f')

def setJPLHorizonsParms(targetID, start, end, incr, jplHorizonsDefaultSettings):

    jplHorizonsSettings = jplHorizonsDefaultSettings
    jplHorizonsSettings['target']['body'] = targetID
    jplHorizonsSettings['date']['start_time'] = processDatetime(start)
    jplHorizonsSettings['date']['stop_time'] = processDatetime(end)
    jplHorizonsSettings['date']['step_size'] = int(incr)
    return jplHorizonsSettings

def jplHorizonsQuery(url, settings):
    cgiSessId = None
    # Iterate through the "settings" data structure and send the
    # information to JPL Horizons so that it knows the target name,
    # date of observation, etc.
    for item in ('ephemerisType', 'tableSettings', 'outputType', 'date', 'target'):
        setting = settings[item]
        # If we have received a CGI session ID from JPL Horizons, set it here 
        if cgiSessId:
            setting['CGISESSID'] = cgiSessId
        # Encode the parameters we want to send into the proper format
        params = urllib.urlencode(setting)
        # Send the request to JPL Horizons using the POST method
        f = urllib.urlopen(url, params)
        # If the is the first time through the loop, we need to
        # extract and save the CGI session ID from the response we got
        # from JPL Horizons.
        if not cgiSessId:
            response = f.read()
            result = re.search('CGISESSID=(\w+)', response)
            cgiSessId = result.group(1)

    # Now that we have told JPL Horizons what we want, we can tell it
    # to generate the ephemeris data.
    params = urllib.urlencode({'go':'Generate Ephemeris', 'CGISESSID': cgiSessId})
    f = urllib.urlopen(url, params)
    # Get the response from JPL Horizons and return it to the caller
    jplHorizonsOutput = f.read()
    return jplHorizonsOutput

def processDatetime(dateTime):
    """
    Returns a Python datetime object.

    Given a date/time, supplied as any any of the following:
    
      - Python datetime object
      - Julian date (JD)
      - Modified Julian date (MJD)
      - YYYYMMDD.DDDD
      - YYYYMMDD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
      - YYYY-MM-DD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
      - YYYY/MM/DD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
      - YYYY-MMM-DD HH:MM

    returns the equivalent date/time, expressed as a Python datetime
    object.

    Args:
        jd: The date/time

    Returns:
        The date/time, expressed as a datetime object
    """
    dateTimeFormats = (
        '%Y%m%d', '%Y-%m-%d', '%Y/%m/%d',
        '%Y%m%d %H', '%Y%m%d %H%M', '%Y%m%d %H%M%S',
        '%Y%m%d %H', '%Y%m%d %H:%M', '%Y%m%d %H:%M:%S',
        '%Y%m%d-%H', '%Y%m%d-%H:%M', '%Y%m%d-%H:%M:%S',
        '%Y-%m-%dT%H', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H', '%Y/%m/%d %H:%M', '%Y/%m/%d %H:%M:%S',
        '%Y-%b-%d %H:%M'
        )

    # if the input value is already a datetime object, just return it.
    if isinstance(dateTime, datetime.datetime):
        return dateTime
    else:
        # The input value might be a JD, MJD, or a YYYYMMDD.DDDD. If
        # it is any of those, we can convert it to a float. If we
        # can't convert it to a float, it must be one of the string
        # representations, e.g., YYYYMMDD HH:MM:SS.
        try:
            dateTime = float(dateTime)
        except ValueError:
            pass

        if isinstance(dateTime, float):
            # The input is a float. Now we have to determine if it is
            # YYYYMMDD.DDDD or JD/MJD.  If the string represention of
            # the date portion of the input is the same length as
            # 'YYYYMMDD', it must be a YYYYMMDD.DDDD. JD and MJD dates
            # are typically either 7 or 5 characters long,
            # respectively, not 8 characters, at least for the range
            # of dates that we usually care about.
            (fracDay, date) = math.modf(dateTime)
            if len(str(int(date))) == len('YYYYMMDD'):
                # Convert input YYYYMMDD.DDDD into datetime object
                return datetime.datetime.strptime(str(int(date)), '%Y%m%d') + datetime.timedelta(days=fracDay)
            else:
                # Input is either JD or MJD. Raise an exception if we
                # slalib isn't available.
                if not jdOk:
                    raise NoSlalibError('Julian dates require slalib, but slalib is not available')
                # For the dates that we care about, if the value is
                # greater than 2400000, we assume that it is a JD, so
                # convert it to an MJD.
                if dateTime > 2400000:
                    dateTime -= 2400000.5
                yy, mm, dd, fracDay, j = slalib.sla_djcl(dateTime - 2400000.5)
                sign, hmsf = slalib.sla_dd2tf(3, fracDay)
                dateStr = '-'.join([str(yy), '%02d' % mm, '%02d' % dd])
                timeStr = ':'.join(['%02d' % hmsf[0], '%02d' % hmsf[1], '%02d' % hmsf[2]])
                dateTimeStr = ' '.join([dateStr, timeStr])
                dateFmt = '%Y-%m-%d %H:%M:%S'
                msec = int(hmsf[3])
                return datetime.datetime.strptime(dateTimeStr, dateFmt) + datetime.timedelta(milliseconds = msec)

        elif isinstance(dateTime, str):
            # The input date is a string. Using one of the acceptable
            # formats, parse it and create a datetime object.
            dateTimeObj = None
            for format in dateTimeFormats:
                try:
                    dateTimeObj = datetime.datetime.strptime(dateTime, format)
                    break
                except ValueError:
                    pass

            # If we were able to parse the input string, return the
            # datetime object. Otherwise, raise an exception.
            if dateTimeObj:
                return dateTimeObj
            else:
                raise DateTimeFormatError('Unexpected date/time format: %s' %dateTime)
        else:
            raise DateTimeFormatError('Unexpected date/time format: %s' %dateTime)

def jplHorizonsGetEphem(start, end, incr, targetName=None, targetID=None, logger=ro.nullLogger()):
    """
    Get ephemeris data from JPL Horizons

    Args:
        start: start time of ephemeris data
        end:        end time of ephemeris data
        incr:       time increment for ephemeris (minutes)
        targetName: The target name to search for in the JPL Object Database
        targetID:   The unique identifier that identifies the target
                    (this can be obtained from jplObjectDBSearch)
        logger:     An ssdlog object

        You can supply either targetName or targetID. Both are keyword
        arguments. If you supply targetName and there are multiple
        targets with that name in the JPL Object Database, you will
        get a MultipleTargetMatchError. targetID is ignored if you
        supply targetName.

        Note that the start and end times can be supplied in many
        different ways:
           - Python datetime object
           - Julian Date
           - Modified Julian date
           - YYYYMMDD.DDDD
           - YYYYMMDD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
           - YYYY-MM-DD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
           - YYYY/MM/DD HH:MM:SS (You can leave off the HH:MM:SS or some subset of that)
           - YYYY-MMM-DD HH:MM
    
    Returns:
        A string containing the output from JPL Horizons

    Raises:
        MultipleTargetMatchError
    """
    if targetName:
        logger.info('targetName is %s' % targetName)
        # Search for the target name in the JPL Object Database
        targetID = jplObjectDBSearch.jplObjectDBSearch(targetName, logger=logger)
    logger.info('targetID is %s' % targetID)
    # If a unique match was found for the targetName or the targetID
    # was supplied as a string, then query JPL Horizons to get the
    # ephemeris data. Otherwise, raise an exception.
    if type(targetID) is str:
        jplHorizonsSettings = setJPLHorizonsParms(targetID, start, end, incr, jplHorizonsDefaultSettings)
        jplHorizonsOutput = jplHorizonsQuery(jplHorizonsURL, jplHorizonsSettings)

        return jplHorizonsOutput
    elif type(targetID) is list:
        raise MultipleTargetMatchError('Multiple objects match supplied target %s: %s' % (targetName, targetID))
    else:
        raise Exception('Unexpected error occurred. Check input parameters')

def selectTargetID(targetID, logger=ro.nullLogger()):
    gotIndex = False
    while not gotIndex:
        print 'Choose a specific target from the following list:'
        i = 1
        for target in targetID:
            print '%3d. %s' % (i, target['name'])
            i += 1
        try:
            index = raw_input('Enter desired target index number (1 <= index <= %d): ' % len(targetID))
            index = int(index)
            if index > 0 and index <= len(targetID):
                gotIndex = True
                target = targetID[index - 1]
            else:
                gotIndex = False
                print '\nError: Index number %d is out of range\n' % index
        except ValueError:
            gotIndex = False
            print '\nError: Unable to parse index number %s\n' % index
        targetID = target['ID']
        logger.info('targetID from list is %s' % targetID)
    return targetID

def main(options, args):
    # Create top level logger.
    logger = ssdlog.make_logger('jplHorizonsIF', options)

    if options.infile:
        # If we were supplied with the name of a JPL Horizons output
        # file, read it here.
        with open(options.infile, 'r') as f:
            jplHorizonsOutput = f.read()

    elif options.targetName:
        # If we were supplied with a targetName, we need to search for
        # the object in the JPL database and then send a query to JPL
        # Horizons.
        if options.start:
            start =  processDatetime(options.start)
        else:
            start = datetime.datetime.utcnow()
        if options.end:
            end =  processDatetime(options.end)
        else:
            if options.duration:
                end = start + datetime.timedelta(hours=float(options.duration))
            else:
                end = start + datetime.timedelta(days=defaultDurationDays, hours=defaultDurationHours)

        # Make sure that the specified object name or ID is recognized
        # by JPL Horizons by searching for the name in both the Major
        # Body list and the Small Body Database Browser
        targetID = jplObjectDBSearch.jplObjectDBSearch(targetName=options.targetName, logger=logger)
        # If we got targetID returned as a string, then there was a
        # unique match for the specified target name and we can just
        # use the targetID as is when querying JPL
        # Horizons. Otherwise, targetID will be a list of matching
        # targets, so we will have to prompt the user to see which one
        # they want.
        if not isinstance(targetID, str):
            targetID = selectTargetID(targetID, logger)
            # With the selected targetID, query the JPL Horizons
            # database again to get the official "Small-Body"
            # designation.
            targetID = jplObjectDBSearch.jplObjectDBSearch(targetID=targetID, logger=logger)
        logger.info('Database targetID is %s' % targetID)
        print 'Sending query to JPL Horizons...'
        jplHorizonsOutput = jplHorizonsGetEphem(start, end, options.incr, targetID=targetID, logger=logger)
        print 'Reply received from JPL Horizons'
        if options.jplOutfile:
            with open(options.jplOutfile, 'w') as f:
                f.write(jplHorizonsOutput)
    else:
        raise MissingInputError('You need to provide either a target name or a filename containing JPL Horizons output')

    jplHorizonsEphem = JPLHorizonsEphem(jplHorizonsOutput, logger)

    if options.outfile:
        TSCTrackFile.writeTSCTrackFile(options.outfile, jplHorizonsEphem.trackInfo, logger)
    else:
        TSCTrackFile.writeTSCTrackOutput(sys.stdout, jplHorizonsEphem.trackInfo, logger)

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
                      help="Input file (output from JPL Horizons - supply either JPL Horizons output or use -t option to supply target name)")
    optprs.add_option("-o", "--out", dest="outfile", default=None,
                      help="Output file (default is to write to stdout)")
    optprs.add_option("--jplOut", dest="jplOutfile", default=None,
                      help="JPL Horizons output file (default is to not write JPL Horizons output)")
    optprs.add_option("-t", "--target", dest="targetName", default=None,
                      help="Target name (to query JPL Horizons - supply either target name or JPL Horizons output)")
    optprs.add_option("--start", dest="start", default=None,
                      help="Start time of tracking output (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD, UTC)")
    optprs.add_option("--end", dest="end", default=None,
                      help="End time of tracking output (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD, UTC)")
    optprs.add_option("--duration", dest="duration", default=None,
                      help="Length of time of tracking output (hours)")
    optprs.add_option("--incr", dest="incr", default=30,
                      help="Step time of tracking output (minutes)")

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

