#!/usr/bin/env python

#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Sep  5 16:29:12 HST 2012
#]

"""
  nstrack.py - Generate non-sidereal tracking coordinates and write
               output to a file in a format compatible with Subaru TSC

  Command-line options:

  Start/end/increment for output:
    --start=<date/time> (start time of output, defaults to current time)
    --end=<date/time>   (end time of output)
    --incr=<value>      (increment between output points, default is 30 minutes)
    --duration=<value>  (duration of observation - can be used instead of
                         specifying end time - default is 1 hour)

  Output options:
    --out=<filename>   (output filename - default is output to screen only)
    --comment=<string> (comment string to write to output file)

  Major body options:
    --sun
    --moon
    --planet --name=<name>
 
    Note that the combination of --planet and --name can be used to
    specify either the name of a planet or the name of a planetary
    satellite, e.g., Deimos, Phobos, etc. See below for a complete list
    of recognized planetary satellites.

  Asteroid options:

    Asteroids can be specified by name or by number or by orbital elements.
  
    --asteroid --name=<name>
    --asteroid --number=<n>
    --asteroid --epoch=<date> --orbinc=<value> --Om=<value> --om=<value> --a=<value> --e=<value> --M=<value> --equinox=<date>

  Comet options:
  
    Comets can be specified by name or by orbital elements.

     --comet --name=<name>
     --comet --epoch=<date> --orbinc=<value> --Om=<value> --om=<value> --q=<value> --e=<value> --Tp=<value> --equinox=<date>

  Orbital elements:
    --epoch   => Epoch date of the elements
    --orbinc  => Inclination wrt ecliptic (deg)
    --Om      => Longitude of ascending node wrt ecliptic (deg)
    --om      => Argument of perihelion wrt ecliptic (deg)
    --a       => Semimajor axis of the orbit (AU) (asteroids)
    --q       => Perihelion distance (AU) (comets)
    --e       => Eccentricity
    --M       => Mean anomaly (deg) (asteroids)
    --Tp      => Perihelion date (comets)
    --equinox => Equinox date of the coordinates (defaults to 2000/1/1)
 
 You can also place all the target information into a text file and
 then use the --infile=<INFILE> option to tell nstrack to read the
 information from the specified file. The input file contains the same
 attribute/value pairs that you would specify on the command-line. An
 example input file might look like this:
 
     asteroid
     name=Ceres
     start='2012-09-01 04:00'
     end='2012-09-01 06:00'

 You can partially specify the name of a comet or asteroid. If more
 than one match is found, nstrack.py will list the targets that
 provide a partial match and then you can choose the exact name of the
 one you want. If the input name matches a single target in the
 datafiles, then that target's information will be used to compute the
 tracking coordinates.

 All date/time entries are UTC and can be YYYYMMDD-HH:MM:SS,
 YYYYMMDD.DDDDD, JD, or MJD

 The following planetary satellites are recognized:
   Mars: Deimos, Phobos
   Jupiter: Io, Europa, Ganymede, Callisto
   Saturn: Mimas, Enceladus, Tethys, Dione, Rhea, Titan, Hyperion, Iapetus
   Uranus: Ariel, Umbriel, Titania, Oberon, Miranda

 This script makes use of the pyephem package
 (http://pypi.python.org/pypi/pyephem/) and the pyslalib package
 (https://github.com/scottransom/pyslalib). Both have to be installed
 in order for nstrack.py to work correctly. It also uses the ssdlog
 and astro.radec modules, which are found in the Subaru Gen2 python
 software directories.
"""

import os, sys, time, datetime, math
import ephem
from pyslalib import slalib
import ssdlog
import astro.radec as radec

# ELEMENTS.* are Asteroid and Comet data files downloaded from JPL
# Horizons: http://ssd.jpl.nasa.gov/?sb_elem
datafilenames = {'asteroid':
                 {'numbered': 'ELEMENTS.NUMBR', 'unnumbered': 'ELEMENTS.UNNUM'},
                 'comet': 'ELEMENTS.COMET'}

defaultDurationDays = 0
defaultDurationHours = 1
defaultEquinox = '2000/1/1'

# Max number of matching targets to list. User can list more than this
# by responding in the affirmative to the prompt.
maxListMatchCount = 100

class UnknownBodyNameError(Exception):
    pass

class UnknownCometError(Exception):
    pass

class MultipleTargetMatchError(Exception):
    def __init__(self, target):
        self.target = target

class UnknownAsteroidError(Exception):
    pass

class UnexpectedDatetimeFormatError(Exception):
    pass

class UnexpectedDatetimeType(Exception):
    pass

class PertelError(Exception):
    pass

def mjd(date):
    """
    Return the Modified Julian Date (MJD).

    Given a date/time, supplied as a Python datetime or ephem.Date
    object, returns the equivalent date/time converted to a float and
    expressed as an MJD.

    Args:
        date: The desired date/time

    Returns:
        The date/time, expressed as an MJD
    """
    if isinstance(date, datetime.datetime):
        (year, month, day, hour, minute, second) = (date.year, date.month, date.day, date.hour, date.minute, date.second)
    elif isinstance(date,ephem.Date):
        (year, month, day, hour, minute, second) = date.tuple()
    else:
        raise UnexpectedDatetimeType('Unexpected date type in mjd: %s' % type(date))
    jd = radec.julianDate(time.strptime('%d-%d-%d %d:%d:%d' % (year, month, day, hour, minute, second), '%Y-%m-%d %H:%M:%S'))
    MJD = jd - 2400000.5
    return MJD

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
                # Input is either JD or MJD
                # For the dates that we care about, if the value is
                # less than 2400000, we assume that it is an MJD, so
                # convert it to a JD.
                if dateTime < 2400000:
                    dateTime += 2400000.5
                # The ephem module provides the Date class, which can
                # be used to convert a floating-point date into a
                # Python datetime object. However, ephem.Date wants
                # the input date as a "Dublin Julian Date", which uses
                # 1899-12-31T12:00:00 as its beginning
                # reference. 1899-12-31T12:00:00 corresponds to
                # JD=2415020.0, so use that value to convert the JD to
                # a DJD and supply that to ephem.Date so that we can
                # use it to create a python datetime object.
                return ephem.Date(dateTime - 2415020.0).datetime()

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
                raise UnexpectedDatetimeFormatError('Unexpected date/time format: %s' %dateTime)
        else:
            raise UnexpectedDatetimeFormatError('Unexpected date/time format: %s' %dateTime)

class SolarSystemBody(object):
    """
    Base class for solar system bodies.
    
    This class is not intended to be used directly. Instead, use one
    of its subclasses, i.e., MajorBody, Asteroid, or Comet.

    Public methods:
        compute: compute the RA/Dec coordinates of the target
        report: writes information about the target to stdout
        writeTrackFile: Write time-history suitable for Subaru TSC
        writeOutput: Write orbital elements and time-history to stdout

    Public attributes:
        elements: input and perturbed orbital elements
        a_ra: astrometric geocentric RA
        a_dec: astrometric geocentric Dec
        g_ra: apparent geocentric RA
        g_dec: apparent geocentric Dec
        earth_distance: distance to Earth (AU)    
    """
    def __init__(self, equinox=None):
        self.a_ra = None
        self.a_dec = None
        self.g_ra = None
        self.g_dec = None
        self.earth_distance = None
        if equinox == None:
            self.equinox = processDatetime(defaultEquinox)
        else:
            self.equinox = processDatetime(equinox)

        # Create the full pathnames to locate the Asteroid and Comet
        # data files. They should be located in either $GENCOMMON/db
        # or, if GEN2COMMON is not defined, in the same directory as
        # nstrack.py.
        try:
            g2common = os.environ['GEN2COMMON']
            dbdir = os.path.join(g2common, 'db')
        except KeyError:
            dbdir = os.path.dirname(sys.argv[0])

        self.datafiles = {}
        for bt in datafilenames:
            if isinstance(datafilenames[bt], dict):
                self.datafiles[bt] = {}
                for t in datafilenames[bt]:
                    self.datafiles[bt][t] = os.path.join(dbdir, datafilenames[bt][t])
            else:
                self.datafiles[bt] = os.path.join(dbdir, datafilenames[bt])

    def compute(self, date):
        """
        Compute the object position on the specified date.

        Args:
            date: the date/time at which to compute the position.
                  Must be specified as a Python datetime object

        Returns:
            Nothing

        Although nothing is returned by compute, it has the side
        effect of setting the following object attributes:
        a_ra - astrometric geocentric RA
        a_dec - astrometric geocentric Dec
        g_ra - apparent geocentric RA
        g_dec - apparent geocentric Dec
        earth_distance - distance to Earth (AU)

        Raises:
            Nothing
        """
        # Call our body's compute method to compute the position on
        # the specified date
        self.body.compute(date)

        # Copy the attributes from the "body" object into our own
        # attributes
        self.a_ra = self.body.a_ra
        self.a_dec = self.body.a_dec
        self.g_ra = self.body.g_ra
        self.g_dec = self.body.g_dec
        # pyephem doesn't seem to have an earth_distance attribute for
        # planetary satellites. If accessing earth_distance raises an
        # exception, set our earth_distance to 0.0.
        try:
            self.earth_distance = self.body.earth_distance
        except AttributeError:
            self.earth_distance = 0.0

    # Compute number of data points in the time-history output
    def _computeNpt(self, start=None, incr=None, end=None, duration=None):
        # If start time is specified, use it. Otherwise, set start to
        # current time.
        if start and len(start) > 0:
            self.start = processDatetime(start)
        else:
            self.start = datetime.datetime.now()

        # If end time is specified, use it. Otherwise, see if a
        # duration was specified. If it was, then use it. If not, use
        # the default deuration.
        if end and len(end) > 0:
            self.end = processDatetime(end)
        else:
            if duration:
                self.end = self.start + datetime.timedelta(hours=float(duration))
            else:
                self.end = self.start + datetime.timedelta(days=defaultDurationDays, hours=defaultDurationHours)

        self.datetimeIncr = datetime.timedelta(minutes = float(incr))
        durationDatetime = self.end - self.start
        total_minutes = durationDatetime.days * 1440.0 + (durationDatetime.seconds + durationDatetime.microseconds / 1000000.0) / 60.0
        self.npt = int(total_minutes / float(incr)) + 1

    # Header for Subaru TSC tracking file
    def _writeHeader(self, file, comment, npt):
        file.write('#%s\n' % comment)
        file.write('+00.0000 +00.0000 ON% +0.000\n')
        file.write('UTC Geocentric Equatorial Mean Polar Geocentric\n')
        file.write('ABS\n')
        file.write('TSC\n')
        file.write('%d\n' % npt)

    # Date format for Subaru TSC tracking file
    def _dateFmt(self, date):
        return '.'.join([date.strftime('%Y%m%d%H%M%S'), '%03d'%(int(date.microsecond / 1000))])

    # RA format for Subaru TSC tracking file
    def _raFmt(self, ra):
        return ' %s' % radec.raDegToString(math.degrees(float(repr(ra))))
    
    # Dec format for Subaru TSC tracking file
    def _decFmt(self, dec):
        return ' %s' % radec.decDegToString(math.degrees(float(repr(dec))))

    # Earth-to-body distance format for Subaru TSC tracking file
    def _distFmt(self, dist):
        return ' %13.9f' % dist
    
    # Equinox format for Subaru TSC tracking file
    def _eqnxFmt(self, eqnx):
        return ' %9.4f' % eqnx

    # Write time-history to specified file object
    def _writeTimeHistory(self, file):
        currentDatetime = self.start
        i = 0
        while (currentDatetime <= self.end):
            self.compute(currentDatetime)
            file.write(self._dateFmt(currentDatetime))
            file.write(self._raFmt(self.a_ra))
            file.write(self._decFmt(self.a_dec))
            file.write(self._distFmt(self.earth_distance))
            file.write(self._eqnxFmt(self.equinox.year))
            file.write('\n')
            i += 1
            currentDatetime = self.start + self.datetimeIncr * i

    def writeTrackFile(self, filename, comment, start, incr, end=None, duration=None):
        """
        Write time-history suitable for Subaru TSC.

        Args:
            filename: output filename
            comment: comment to write into the first line of the output file
            start: start date/time for time-history
            incr: step increment for time-history (minutes)
            end: end date/time for time-history
            duration: duration of time-history (hours)

        You must supply filename, comment, start, and incr. You can
        choose to supply either end or duration. start and end are UTC
        and can be supplied as YYYYMMDD-HH:MM:SS, YYYYMMDD.DDDDD, JD,
        or MJD.

        Returns:
            Nothing

        Raises:
            Nothing
        """
        self._computeNpt(start, incr, end, duration)
        # Write header and time-history suitable for Subaru TSC to
        # specified file
        with open(filename, 'w') as outfile:
            self._writeHeader(outfile, comment, self.npt)
            self._writeTimeHistory(outfile)
        print '\nOutput written to', filename

    # Write orbital elements and time-history to stdout
    def writeOutput(self, start, incr, end=None, duration=None):
        """
        Write orbital elements and time-history to stdout.

        Args:
            start: start date/time for time-history
            incr: step increment for time-history (minutes)
            end: end date/time for time-history
            duration: duration of time-history (hours)

        You must supply start, and incr. You can choose to supply
        either end or duration. start and end are UTC and can be
        supplied as YYYYMMDD-HH:MM:SS, YYYYMMDD.DDDDD, JD, or MJD.

        Returns:
            Nothing

        Raises:
            Nothing
        """
        self._computeNpt(start, incr, end, duration)
        self.compute(self.start)
        self.report()
        self._writeTimeHistory(sys.stdout)

    def report(self):
        """
        Stub that will be overridden by subclasses.
        """
        pass

class MajorBody(SolarSystemBody):
    """
    Encapsulates sun, moon, planets, and planetary satellites targets.

    Inherits functions and attributes from SolarSystemBody.
    """
    def __init__(self, name, equinox=None):
        super(MajorBody, self).__init__(equinox)
        try:
            self.body = eval('ephem.%s()' % name.capitalize())
        except AttributeError:
            raise UnknownBodyNameError('Unknown body name: %s' % name)

    def compute(self, date):
        # Call our parent's compute method to compute the position on
        # the specified date
        super(MajorBody, self).compute(date)

    def report(self):
        """
        Print the body name to stdout.
        """
        print '\n',self.body.name,'\n'

class MinorBody(SolarSystemBody):
    """
    Base class for solar system minor bodies.
    
    This class is not intended to be used directly. Instead, use one
    of its subclasses, i.e., Asteroid, or Comet.

    Inherits functions and attributes from SolarSystemBody. Additional
    public attributes are listed below.

    Public attributes:
        elements: input and perturbed orbital elements
    """
    jform = None
    bodyDescr = 'MinorBody'

    def __init__(self, equinox=None):
        super(MinorBody, self).__init__(equinox)
        self.body = ephem.EllipticalBody()
        self.elements = {
            'w':          {'Descr': 'Argument of perihelion (deg) (om)     ', 'input': None, 'perturbed': None},
            'Node':       {'Descr': 'Longitude of ascending node (deg) (Om)', 'input': None, 'perturbed': None},
            'i':          {'Descr': 'Inclination (deg) (orbinc)            ', 'input': None, 'perturbed': None},
            'e':          {'Descr': 'Eccentricity (e)                      ', 'input': None, 'perturbed': None},
            'M':          {'Descr': 'Mean anomaly (deg) (M)                ', 'input': None, 'perturbed': None},
            'epoch':      {'Descr': 'Epoch of the elements (epoch)         ', 'input': None, 'perturbed': None},
            'epoch (JD)': {'Descr': 'Epoch of the elements (JD)            ', 'input': None, 'perturbed': None},
            }
        self.reference = None
        self.matchCount = 0
        self.matchingNames = []

    def _processFileHeader(self, datafile):
        # This method reads the first two lines of the datafile and
        # parses them so that we can know the name of each data column
        # and the start/end of each data column.  We assume that the
        # datafile has been opened and the file pointer is positioned
        # at the first line of the file.
        
        # The first line in the file is the header that indicates what
        # is in each column.
        header = datafile.readline()

        # The second line is a separator between the header and the
        # data. The width of each data column is defined by the length
        # of each separator string.
        separator = datafile.readline()

        # Split the header and separator lines into their individual
        # elements.
        headers = header.split()
        separators = separator.split()

        # Unfortunately, the column headers aren't completely
        # consistent between the ELEMENTS.NUMBR, ELEMENTS.UNNUM, and
        # ELEMENTS.COMET files. In ELEMENTS.NUMBR, the first column is
        # "Num" and the second is "Name" which is ok. In
        # ELEMENTS.UNNUM, the first column is "Designation", so we
        # will change it to be "Name", to be consistent with
        # ELEMENTS.NUMBR.
        if headers[0] == 'Designation':
            headers[0] = 'Name'

        # The header of the ELEMENTS.COMET data file starts with 'Num
        # Name' over the first column of the separators, so there are
        # actually more headers than separators. We want a one-to-one
        # relationship between the headers and columns, so remove the
        # first header, i.e., the 'Num' string.
        if len(headers) > len(separators):
            headers.pop(0)

        # Create the "columns" data structure that contains the name
        # of each column (from the header) and the start/end of each
        # column (from the separator).
        columns = {}
        i = 0
        start = 0
        for sep in separators:
            end = start + len(sep)
            columns[headers[i]] = {'Name': headers[i], 'start': start, 'end': end}
            start = end + 1
            i += 1

        # Return the list of headers and the columns data structure
        return headers, columns

    def _findMatchingNames(self, name, datafileName):
        # Search through the datafile for names that are at least a
        # partial match of the supplied name. Keep track of the number
        # of matches in our matchCount attribute and the list of
        # matching names in our matchingNames attribute.
        values = {}
        with open(datafileName, 'r') as datafile:
            headers, columns = self._processFileHeader(datafile)
            line = datafile.readline()
            while line:
                # Get the Name of this object
                values['Name'] = line[columns['Name']['start']:columns['Name']['end']].strip()
                # See if the supplied name is at least a partial match
                # to the object name.
                if name.lower() in values['Name'].lower():
                    self.matchCount += 1
                    self.matchingNames.append(values['Name'])
                line = datafile.readline()

    def setElements(self, Type, om, Om, orbinc, e, M, aorq, epoch, epoch_M):

        # The eccentricity value determines what type of body we need
        # to create.
        if float(e) < 1.0:
            self.body = ephem.EllipticalBody()
        elif float(e) == 1.0:
            self.body = ephem.ParabolicBody()
        elif float(e) > 1.0:
            self.body = ephem.HyperbolicBody()

        # Set the orbital element values in our elements attribute
        self.elements['w'][Type] = float(om)
        self.elements['Node'][Type] = float(Om)
        self.elements['i'][Type] = float(orbinc)
        self.elements['e'][Type] = float(e)
        self.elements['M'][Type] = float(M)
        if self.jform == 2: # asteroid
            self.elements['a'][Type] = float(aorq)
        elif self.jform == 3: # comet
            self.elements['q'][Type] = float(aorq)
        self.elements['epoch'][Type] = processDatetime(epoch)
        self.elements['epoch_M'][Type] = processDatetime(epoch_M)
        self.elements['epoch (JD)'][Type] = mjd(processDatetime(epoch)) + 2400000.5
        self.elements['epoch_M (JD)'][Type] = mjd(processDatetime(epoch_M)) + 2400000.5

        # Set the orbital element values in the body object
        self.body._om = self.elements['w'][Type] # Argument of perihelion (deg)
        self.body._Om = self.elements['Node'][Type] # Longitude of ascending node (deg)
        self.body._inc = self.elements['i'][Type] # Inclination (deg)
        if isinstance(self.body, ephem.EllipticalBody) or isinstance(self.body, ephem.HyperbolicBody):
            self.body._e = self.elements['e'][Type] # Eccentricity
        if self.jform == 2: # asteroid
            self.body._M = self.elements['M'][Type]
            self.body._a = self.elements['a'][Type]
            self.body._epoch_M = self.elements['epoch_M'][Type]
        elif self.jform == 3: # comet
            if isinstance(self.body, ephem.EllipticalBody):
                self.body._M = 0.0
                self.body._a = self.elements['q'][Type] / (1 - self.elements['e'][Type])
                self.body._epoch_M = self.elements['epoch_M'][Type]
            else: # ParabolicBody and HyperbolicBody
                self.body._q = self.elements['q'][Type]
                self.body._epoch_p = self.elements['epoch_M'][Type]
        self.body._epoch = self.equinox # pyephem docs say "Epoch for _inc, _Om, and _om", but equinox works better here

    def pertel(self, date):
        """
        Perturb the orbital elements to the specified date

        Args:
            date: the date/time to which we want to perturb the
                  elements
        Returns:
            Nothing

        Although nothing is returned by pertel, it has the side effect
        of setting the 'perturbed' items in the elements attribute.

        Raises:
            PertelError: an error occurred when perturbing the elements
        """
        # sla_pertel error messages
        msg = {
            102: 'warning, distant epoch',
            101: 'warning, large timespan (>100 years)',
             -1: 'illegal JFORM',
             -2: 'illegal E0',
             -3: 'illegal AORQ0',
             -4: 'internal error',
             -5: 'numerical error',
            }
        for i in range(1,11):
            msg[i] = 'coincident with major planet'

        # sla_pertel wants epoch and date as Terrestrial Time(TT), but
        # pyephem uses UTC. Compute the date and epoch as TT.
        date_tt = mjd(date) + slalib.sla_dtt(mjd(date)) / 86400.0
        mjd_epoch = mjd(self.elements['epoch']['input'])
        epoch_tt = mjd_epoch + slalib.sla_dtt(mjd_epoch)/ 86400.0
        mjd_epoch_M = mjd(self.elements['epoch_M']['input'])
        epoch_M_tt = mjd_epoch_M + slalib.sla_dtt(mjd_epoch_M) / 86400.0
        om = math.radians(self.elements['w']['input'])
        Om = math.radians(self.elements['Node']['input'])
        inc = math.radians(self.elements['i']['input'])
        e = self.elements['e']['input']
        if self.jform == 2: # asteroid
            aorq = self.elements['a']['input']
        elif self.jform == 3: # comet
            aorq = self.elements['q']['input']
        M = math.radians(self.elements['M']['input'])

        # Call sla_pertel to perturb the orbital elements
        (epoch, inc, Om, om, aorq, e, M, jstat) = slalib.sla_pertel(self.jform, epoch_tt, date_tt, epoch_M_tt, inc, Om, om, aorq, e, M)

        # Non-zero jstat indicates that an error occurred
        if jstat < 0:
            # Fatal error
            raise PertelError('jstat %d %s' % (jstat, msg[jstat]))

        if jstat > 0:
            # Warning
            print 'sla_pertel:', msg[jstat]

        # Save the perturbed orbital element values
        epoch_M = processDatetime(epoch - slalib.sla_dtt(epoch) / 86400.0)
        self.setElements('perturbed', math.degrees(om), math.degrees(Om), math.degrees(inc), e, math.degrees(M), aorq, self.equinox, epoch)

    def compute(self, date):
        # Perturb the orbital elements to the specified date
        self.pertel(date)

        # Call our parent's compute method to compute the position on
        # the specified date
        super(MinorBody, self).compute(date)

    def report(self):
        # Print the orbital elements to stdout
        fw1 = 38
        fw2 = 26
        title = self.bodyDescr + ' orbital elements'
        print ' '
        print '%s  %s  %s' % (title.ljust(fw1), 'Input'.ljust(fw2), 'Perturbed to date'.ljust(fw2))
        print '%s  %s  %s' % ('----------------------'.ljust(fw1), '-----'.ljust(fw2), '-----------------'.ljust(fw2))
        for name in self.reportElemList:
            print '%s  %s  %s' % (self.elements[name]['Descr'].ljust(fw1),str(self.elements[name]['input']).ljust(fw2),str(self.elements[name]['perturbed']).ljust(fw2))
        print ' '

class Comet(MinorBody):
    """
    Encapsulates comet targets.

    Inherits functions and attributes from MinorBody.
    """
    jform = 3
    bodyDescr = 'Comet'
    reportElemList = ('w', 'Node', 'i', 'e', 'q', 'epoch_M', 'epoch_M (JD)', 'epoch', 'epoch (JD)')

    def __init__(self, name=None, om=None, Om=None, orbinc=None, e=None, q=None, epoch=None, Tp=None, equinox=None):
        """
        Initializes Comet object.

        Args:
            name: Comet name
            om: Argument of perihelion (deg)
            Om: Longitude of ascending node wrt ecliptic (deg)
            orbinc: Inclination wrt ecliptic (deg)
            e: Eccentricity
            q: Perihelion distance (AU)
            epoch: Epoch date of the elements
            Tp: Perihelion date
            equinox: Equinox date of the coordinates

        To define the comet, you can choose to specify either the
        comet name, in which case the orbital elements will be fetched
        from the ELEMENTS.COMET file, or the orbital elements. The
        date/time quantities are UTC and can be specified as
        YYYYMMDD-HH:MM:SS, YYYYMMDD.DDDDD, JD, or MJD.

        Returns:
            A Comet object

        Raises:
            UnknownCometError: Comet name not found in ELEMENTS.COMET file
        """
        super(Comet, self).__init__(equinox)
        self.elements['q']            = {'Descr': 'Perihelion distance (AU) (q)', 'input': None, 'perturbed': None}
        self.elements['epoch_M']      = {'Descr': 'Date of perihelion (Tp)     ', 'input': None, 'perturbed': None}
        self.elements['epoch_M (JD)'] = {'Descr': 'Date of perihelion (JD)     ', 'input': None, 'perturbed': None}
        self.bodyName = None

        # If a comet name was supplied, try to read the orbital
        # elements from the comet datafile.
        if name:
            # First, try to find some objects in the ELEMENTS.COMET
            # datafile that match the supplied name.
            self._findMatchingNames(name, self.datafiles['comet'])
            if self.matchCount == 0:
                # Raise an exception if we didn't find any matches.
                raise UnknownCometError('Unknown comet name: %s' % name)
            elif self.matchCount == 1:
                # We found a single match, so we can use that name to
                # get the orbital elements from the datafile.
                (om, Om, orbinc, e, q, epoch, Tp) = self._getElementsFromFile(self.matchingNames[0])
            else:
                # More than one matching name found. Raise a
                # MultipleTargetMatchError and let caller decide what
                # to do.
                raise MultipleTargetMatchError(self)

        # Set our attributes to the input orbital elements. However,
        # they will have to be perturbed to the observation date
        # before they can be used to compute the comet position.
        self.setElements('input', om, Om, orbinc, e, 0.0, q, epoch, Tp)

    def _getElementsFromFile(self, name):
        # Read comet orbital elements from the datafile. We have to
        # search in the datafile to find the specified name.
        nameFound = False
        values = {}
        with open(self.datafiles['comet'], 'r') as cometFile:
            headers, columns = self._processFileHeader(cometFile)
            line = cometFile.readline()
            while not nameFound and line:
                # Get the Name of this comet
                values['Name'] = line[columns['Name']['start']:columns['Name']['end']].strip()
                values['Ref'] = line[columns['Ref']['start']:columns['Ref']['end']].rstrip()

                # See if this comet is the one we are looking for
                if values['Name'].lower() == name.lower():
                    # We found the comet we were looking for, so
                    # copy the data from the line and put it into the
                    # appropriate element of the values data
                    # structure.
                    nameFound = True
                    for headerName in headers:
                        values[headerName] = line[columns[headerName]['start']:columns[headerName]['end']].strip()
                else:
                    line = cometFile.readline()

        if nameFound:
            # We found the comet, so return the values we read from
            # the file.
            self.bodyName = values['Name']
            self.reference = values['Ref']
            return (values['w'], values['Node'], values['i'], values['e'], values['q'], values['Epoch'], values['Tp'])
        else:
            # We didn't find the comet, so raise an exception.
            raise UnknownCometError('Unknown comet name: %s' % name)

    def report(self):
        """
        Print the comet orbital elements and other information to
        stdout.
        """
        print ' '
        if self.bodyName:
            print '%s Ref: %s' % (self.bodyName, self.reference)
        else:
            print 'User-defined body'
        super(Comet, self).report()

class Asteroid(MinorBody):
    """
    Encapsulates asteroid targets.

    Inherits functions and attributes from MinorBody.
    """
    jform = 2
    bodyDescr = 'Asteroid'
    reportElemList = ('w', 'Node', 'i', 'e', 'a', 'M', 'epoch', 'epoch (JD)')
    
    def __init__(self, name=None, number=None, M=None, om=None, Om=None, orbinc=None, e=None, a=None, epoch=None, equinox=None):
        """
        Initializes Asteroid object.

        Args:
            name: Asteroid name
            number: Asteroid number
            M: mean anomaly (deg)
            om: Argument of perihelion (deg)
            Om: Longitude of ascending node wrt ecliptic (deg)
            orbinc: Inclination wrt ecliptic (deg)
            e: Eccentricity
            a: Semimajor axis of the orbit (AU)
            epoch: Epoch date of the elements
            equinox: Equinox date of the coordinates

        To define the asteroid, you can choose to specify either the
        asteroid name or number, in which case the orbital elements
        will be fetched from the ELEMENTS.NUMBR or ELEMENTS.UNNUM
        file, or the orbital elements. The date/time quantities are
        UTC and can be specified as YYYYMMDD-HH:MM:SS, YYYYMMDD.DDDDD,
        JD, or MJD.

        Returns:
            An Asteroid object

        Raises:
            UnknownAsteroidError: Asteroid name or number not found in
            ELEMENTS.NUMBR or ELEMENTS.UNNUM file
        """
        super(Asteroid, self).__init__(equinox)
        self.elements['a']            = {'Descr': 'Semimajor axis of the orbit (AU) (a)', 'input': None, 'perturbed': None}
        self.elements['epoch_M']      = {'Descr': 'Epoch of the elements (epoch)       ', 'input': None, 'perturbed': None}
        self.elements['epoch_M (JD)'] = {'Descr': 'Epoch of the elements (JD)          ', 'input': None, 'perturbed': None}
        self.bodyName = None
        self.bodyNumber = None

        if name:
            # If we have an asteroid name, first try to find the any
            # matching asteroid(s) in the "numbered" and the
            # "unnumbered" file
            self._findMatchingNames(name, self.datafiles['asteroid']['numbered'])
            matchCountNum = self.matchCount
            self._findMatchingNames(name, self.datafiles['asteroid']['unnumbered'])
            matchCountUnnum = self.matchCount - matchCountNum

            if self.matchCount == 0:
                # We didn't find any matching asteroids, so raise an
                # exception.
                raise UnknownAsteroidError('Unknown asteroid name: %s' % name)
            elif self.matchCount == 1:
                # We found a single matching asteroid
                if matchCountNum == 1:
                    # If we found a single match and it was in the
                    # "numbered" file, get the orbital elements from
                    # that file.
                    (om, Om, orbinc, e, M, a, epoch) = self._getElementsFromFile(self.datafiles['asteroid']['numbered'], name=self.matchingNames[0])
                if matchCountUnnum == 1:
                    # If we found a single match and it was in the
                    # "unnumbered" file, get the orbital elements from
                    # that file.
                    (om, Om, orbinc, e, M, a, epoch) = self._getElementsFromFile(self.datafiles['asteroid']['unnumbered'], name=self.matchingNames[0])
            else:
                # More than one matching name found. Raise a
                # MultipleTargetMatchError and let caller decide what
                # to do.
                raise MultipleTargetMatchError(self)

        elif number:
            # If we have the asteroid number, the only choice is to
            # look in the "numbered" file
            (om, Om, orbinc, e, M, a, epoch) = self._getElementsFromFile(self.datafiles['asteroid']['numbered'], number=number)

        # Set our attributes to the input orbital elements. However,
        # they will have to be perturbed to the observation date
        # before they can be used to compute the comet position.
        self.setElements('input', om, Om, orbinc, e, M, a, epoch, epoch)

    def _getElementsFromFile(self, filename, name=None, number=None):
        # Read asteroid orbital elements from the datafile. We have to
        # search in the datafile to find the specified name.
        itemFound = False
        values = {}
        with open(filename, 'r') as asteroidFile:
            
            headers, columns = self._processFileHeader(asteroidFile)

            line = asteroidFile.readline()
            while not itemFound and line:
                # Get the Name and/or Number of this asteroid
                if 'Num' in headers:
                    values['Num'] = line[columns['Num']['start']:columns['Num']['end']].strip()
                values['Name'] = line[columns['Name']['start']:columns['Name']['end']].strip()
                    
                values['Ref'] = line[columns['Ref']['start']:columns['Ref']['end']].rstrip()

                # See if this asteroid is the one we are looking for
                if (name and values['Name'].lower() == name.lower()) or \
                       (number and values['Num'] == number):
                    # We found the asteroid we were looking for, so
                    # copy the data from the line and put it into the
                    # appropriate element of the values data
                    # structure.
                    itemFound = True
                    for headerName in headers:
                        values[headerName] = line[columns[headerName]['start']:columns[headerName]['end']].strip()
                else:
                    # We didn't find the asteroid, so read the next
                    # line in the file.
                    line = asteroidFile.readline()

        if itemFound:
            # We found the asteroid, so return the values we read from
            # the file.
            self.bodyName = values['Name']
            self.reference = values['Ref']
            if 'Num' in values:
                self.bodyNumber = values['Num']
            self.magnitude = values['H']
            return (values['w'], values['Node'], values['i'], values['e'], values['M'], values['a'], values['Epoch'])
        else:
            # We didn't find the asteroid, so raise an exception.
            if name:
                raise UnknownAsteroidError('Unknown asteroid name: %s' % name)
            else:
                raise UnknownAsteroidError('Unknown asteroid number: %s' % number)

    def report(self):
        """
        Print the asteroid orbital elements and other information to
        stdout.
        """
        print ' '
        if self.bodyName and self.bodyNumber:
            print self.bodyNumber, self.bodyName, 'MG=', self.magnitude, 'Ref:', self.reference
        elif self.bodyName:
            print self.bodyName, 'MG=', self.magnitude, 'Ref:', self.reference
        else:
            print 'User-defined body'
        super(Asteroid, self).report()

def planet(options, args):
    # Create and return a MajorBody object. This is used for the sun,
    # moon, planets, and planetary satellites.
    if options.sun:
        name = 'Sun'
    if options.moon:
        name = 'Moon'
    if options.planet:
        name = options.name
    return MajorBody(name)

def comet(options, args):
    # Create and return a Comet object.
    if len(options.name) > 0:
        return Comet(name = options.name)
    else:
        return Comet(om=options.om, Om=options.Om, orbinc=options.orbinc, e=options.e, q=options.q, epoch=options.epoch, Tp=options.Tp)

def asteroid(options, args):
    # Create and return an Asteroid object.
    if len(options.name) > 0:
        return Asteroid(name = options.name)
    elif len(options.number) > 0:
        return Asteroid(number = options.number)
    else:
        return Asteroid(M=options.M, om=options.om, Om=options.Om, orbinc=options.orbinc, e=options.e, a=options.a, epoch=options.epoch)

def readOptionsFromFile(optprs, infile):
    # Read the program options from the specified file
    opts = []
    with open(infile) as inFile:
        for inputLine in inFile:
            if inputLine[0:2] != '--':
               inputLine = '--' + inputLine
            opts.append(inputLine.strip().replace('"','').replace("'",''))
    (options, args) = optprs.parse_args(opts)
    return options

def resolveMatchingNames(name, target):
    print '%d matching %s items found for input name %s' % (target.matchCount, target.bodyDescr, name)
    if target.matchCount > maxListMatchCount:
        sys.stdout.write('Do you want to list them all? ')
        response = sys.stdin.readline()
    else:
        response = 'y'
    if 'y' in response.lower():
        index = 1
        for name in target.matchingNames:
            print '%3d. %s' % (index, name)
            index += 1
        sys.stdout.write('Enter index number of the %s you want to use (or Ctrl-C to quit): ' % target.bodyDescr)
        try:
            index = int(sys.stdin.readline())
        except KeyboardInterrupt:
            print 'Goodbye!'
            sys.exit(1)
        except ValueError:
            raise Exception('Index number must be in range 1 <= index <= %d' % len(target.matchingNames))

        if index > 0 and index <= len(target.matchingNames):
            exactName = target.matchingNames[index - 1]
            return exactName
        else:
            raise Exception('Index number must be in range 1 <= index <= %d' % len(target.matchingNames))
    else:
        print 'Modify your --name argument to more closely match available %s names' % target.bodyDescr
        return None

def processTarget(options, args):
    if options.sun or options.moon or options.planet:
        target = planet(options, args)
    elif options.asteroid:
        target = asteroid(options, args)
    elif options.comet:
        target = comet(options, args)
    else:
        raise Exception('No target specified')

    target.writeOutput(options.start, options.incr, options.end, options.duration)

    if options.out:
        target.writeTrackFile(options.out, options.comment, options.start, options.incr, options.end, options.duration)

def main(options, args):

    # First, try to process the target with the supplied options
    try:
        processTarget(options, args)
    except MultipleTargetMatchError as e:
        # If we got a MultipleTargetMatchError, try to resolve the
        # name into one that will result in a unique match. If
        # successful, process the target again with the unique name.
        options.name = resolveMatchingNames(options.name, e.target)
        if options.name != None:
            processTarget(options, args)

if __name__ == '__main__':

    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--infile", dest="infile", default=None,
                      help="Filename with input data")
    optprs.add_option("--comment", dest="comment", default='<No comment>',
                      help="Comment to place in the output file")
    optprs.add_option("--out", dest="out", default=None,
                      help="Output filename")
    optprs.add_option("--sun", dest="sun", action="store_true", default=False,
                      help="Specify the sun as the object to track")
    optprs.add_option("--moon", dest="moon", action="store_true", default=False,
                      help="Specify the moon as the object to track")
    optprs.add_option("--planet", dest="planet", action="store_true", default=False,
                      help="Specify a planet as the object to track")
    optprs.add_option("--name", dest="name", default='',
                      help="Name of object to track (planet, asteroid, or comet name)")
    optprs.add_option("--number", dest="number", default='',
                      help="Number of object to track (asteroid number)")
    optprs.add_option("--asteroid", dest="asteroid", action="store_true", default=False,
                      help="Specify an asteroid as the object to track")
    optprs.add_option("--comet", dest="comet", action="store_true", default=False,
                      help="Specify a comet as the object to track")
    optprs.add_option("--start", dest="start", default=None,
                      help="Start time of tracking output (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD)")
    optprs.add_option("--end", dest="end", default=None,
                      help="End time of tracking output (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD)")
    optprs.add_option("--duration", dest="duration", default=None,
                      help="Length of time of tracking output (hours)")
    optprs.add_option("--incr", dest="incr", default=30,
                      help="Step time of tracking output (minutes)")
    optprs.add_option("--equinox", dest="equinox", default=defaultEquinox,
                      help="Equinox of the coordinates (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD)")
    optprs.add_option("--epoch", dest="epoch", 
                      help="Epoch of the elements (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD)")
    optprs.add_option("--orbinc", dest="orbinc", 
                      help="Inclination of the orbit (deg)")
    optprs.add_option("--Om", dest="Om", 
                      help="Longitude of the ascending node (deg)")
    optprs.add_option("--om", dest="om", 
                      help="Argument of perihelion (deg)")
    optprs.add_option("-a", "--a", dest="a", 
                      help="Semi-major axis (mean distance) (AU) (asteroids)")
    optprs.add_option("-q", "--q", dest="q", 
                      help="Perihelion distance (AU) (comets)")
    optprs.add_option("-e", "--e", dest="e", 
                      help="Eccentricity of the orbit")
    optprs.add_option("-M", "--M", dest="M", 
                      help="Mean anomaly at epoch (deg) (asteroids)")
    optprs.add_option("--Tp", dest="Tp", 
                      help="Time of perihelion passage (comets) (JD or MJD or YYYY-MM-DD HH:MM:SS or YYYYMMDD.DDDDD)")
    
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if options.infile:
        options = readOptionsFromFile(optprs, options.infile)

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
