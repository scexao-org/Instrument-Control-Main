#!/usr/bin/env python

#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Mar  6 15:51:35 HST 2013
#]

import os, sys, re
import urllib
import remoteObjects as ro
import ssdlog

"""
  jplObjectDBSearch.py -

                         Provides an interface to the JPL Object
                         Database, which includes both the JPL Major
                         Body targets and the JPL Small Body Database
                         Browser (SBDB). This module is useful in
                         combination with the jplHorizonsIF.py module
                         because it provides a way to search for a
                         planet, planetary moon, comet or asteroid and
                         get the identifier by which the JPL Horizons
                         system catalogues the object.

  Command-line options (supply either of the following):
    -t <target>     (Solar system planet, planetary moon, comet, or asteroid name)
    -i <identifier> (identifier as returned by the SBDB when multiple matches are found)

     When supplied with a target name, jplObjectDBSearch writes to
     stdout either the unique MB (Major Body) identifier or a list of
     the matching small body objects. If a list is returned, the ID
     values in the list can be used to query the SBDB again to get the
     unique SB (Small Body) identifier.

  From a python script, you can use the jplObjectDBSearch module as
  follows:

  import astro.jplObjectDBSearch as jplObjectDBSearch
  targetID = jplObjectDBSearch.jplObjectDBSearch(targetName='Jupiter')

  If targetID is returned as a string, the specified target was
  located uniquely in the database. If targetID is returned as a list,
  then it will contain the identifiers and names of all the matching
  targets. You can use the ID value of a target from the list to get
  the unique identifier of the desired target. For example:

  import astro.jplObjectDBSearch as jplObjectDBSearch
  targetID = jplObjectDBSearch.jplObjectDBSearch(targetName='Harrington')
  uniqueID = jplObjectDBSearch.jplObjectDBSearch(targetID=targetID[0]['ID'])

"""

jplSmallBodyDBurl = 'http://ssd.jpl.nasa.gov/sbdb.cgi'

# We expect the JPL Horizons Major Bodies list to be in the file
# $GEN2COMMON/db/jplHorizonsMB.dat.
g2common = os.environ['GEN2COMMON']
mbDatafile = os.path.join(g2common, 'db', 'jplHorizonsMB.dat')

class NoMatchTargetError(Exception):
    pass

class MissingInputError(Exception):
    pass

def jplSmallBodyDBQuery(url, sstr=None, ID=None):
    # Send a query to the JPL Small Body Database Browser to search
    # for the specified target, which can be supplied as either a
    # search string (sstr) or an ID. If a search string is supplied,
    # the browser might return multiple matching targets but the ID is
    # a unique alpha-numeric identifier for a particular target.
    if sstr:
        params = {'sstr': sstr}
    elif ID:
        params = {'ID': ID}

    # Send the request to JPL Small Body Database Browser using the
    # POST method
    f = urllib.urlopen(url, urllib.urlencode(params))

    # Get the response from JPL Small Body Database Browser and return
    # it to the caller
    jplSmallBodyDBOutput = f.read()
    return jplSmallBodyDBOutput

def locateLine(lines, startNum, regexp):
    # Starting at line number startNum, locate the first line in the
    # lines array that matches the supplied regular
    # expression. Returns the line number with the match, or None if
    # none of the lines matched.
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

def parseJPLSmallBodyDBOutput(jplSmallBodyDBOutput):
    # Parse the output returned from the JPL Small Body Database
    # Browser to see if there was a single match or multiple
    # matches. Returns either the unique match or a list of the
    # matching targets.

    # Split the output returned from the JPL Small Body Database
    # Browser into separate lines.
    lines = jplSmallBodyDBOutput.split('\n')

    # First, check the output to see if there was an error, i.e., no
    # match found. If so, raise an Exception.
    noMatchFoundLineNum = locateLine(lines, 0, re.compile('No Matching Record:'))
    if noMatchFoundLineNum:
        line = lines[noMatchFoundLineNum]
        match = re.search('search string = "<b>(.*)</b>"', line)
        raise NoMatchTargetError('No match found for specified target %s in JPL Small Body Database' %  match.group(1))

    # Check the output to see if there were multiple matches
    # returned. If so, return a list with the results. Each item in
    # the list is a dict with the following two keys:
    # 'ID': <alpha-numeric identifier>
    # 'name': <human-readable description>
    multMatchFoundLineNum = locateLine(lines, 0, re.compile('Please select from the list below.'))
    if multMatchFoundLineNum:
        matchList = []
        tableStartLineNum = locateLine(lines, multMatchFoundLineNum, re.compile('^<table .*>'))
        tableEndLineNum = locateLine(lines, tableStartLineNum, re.compile('^</table>'))
        for i in range(tableStartLineNum, tableEndLineNum):
            test = re.search('<td><a href="(.*)">(.*)</a></td>', lines[i])
            if test:
                url, IDstr = test.group(1).split('?')
                junk, ID = IDstr.split('=')
                name = test.group(2)
                matchList.append({'ID': ID, 'name': name})
        return matchList

    # If we get here, the JPL Small Body Database Browser found an
    # exact match for the supplied input. Parse the results to get the
    # string that will identify the object to JPL Horizons. The
    # identifier is a combination of the values in the body_group and
    # sstr fields.
    pattern = '<a href=".*find_body=.*&amp;body_group=(.*)&amp;sstr=(.*?)">'
    identifierLineNum = locateLine(lines, 0, re.compile(pattern))
    if identifierLineNum:
        line = lines[identifierLineNum]
        match = re.search(pattern, line)
        body_group = match.group(1).upper()
        sstr = match.group(2).replace('[', ' ').replace(']', ' ').strip()
        return ':'.join([body_group, sstr])

def searchJplHorizonsMB(targetName):
    # Search the file containing the list of JPL Horizons Major Bodies
    # to see if we can find the supplied name. If we find it, return
    # the identifier describing the body, which will be something like
    # MB:499 (the ID for Mars). Otherwise, return None for the ID.
    mbID = None
    itemFound = False

    with open(mbDatafile, 'r') as f:
        # The first line in the file is the header that indicates what
        # is in each column.
        header = f.readline()

        # The second line is a separator between the head and the
        # data. The width of each column is defined by the length of
        # each separator string.
        separator = f.readline()

        # Split the header and separator lines into their individual
        # elements.
        headers = header.split()
        separators = separator.split()

        # Create the "columns" data structure that contains the name
        # of each column (from the header) and the start/end of each
        # column (from the separator).
        columns = {}
        i = 0
        start = header.find('ID#')
        for sep in separators:
            end = start + len(sep)
            columns[headers[i]] = {'Name': headers[i], 'start': start, 'end': end}
            start = end + 1
            i += 1

        line = f.readline()
        while not itemFound and line:
            name = line[columns['Name']['start']:columns['Name']['end']].strip()
            designation = line[columns['Designation']['start']:columns['Designation']['end']].strip()
            if (len(name) > 0 and name.lower() == targetName.lower()) or \
               (len(designation) > 0 and designation.lower() == targetName.lower()):
                itemFound = True
                ID = line[columns['ID#']['start']:columns['ID#']['end']].strip()
                mbID = ':'.join(['MB', ID])
            else:
                line = f.readline()
        
    return mbID

def jplObjectDBSearch(targetName=None, targetID=None, logger=ro.nullLogger()):
    """
    Search the JPL Object Database for the specified target.

    Args:
        targetName: The target name to search for in the JPL Object Database
        targetID:   The unique identifier that identifies the target (JPL SBDB identifier)

        You can supply either targetName or targetID. Both are keyword
        arguments. If you supply targetName and targetID, targetID
        will be ignored.

    Returns:
        targetID

        If targetName was supplied and it resulted in a unique match
        in the database, then targetID is returned as the unique
        identifier for the target in the JPL Horizons system. If
        targetName resulted in multiple matches in the database, then
        targetID is returned as a list of the matching objects. Eath
        item in the list is a dict with the following keys:

        ID => identifier of the object in the JPL Small Body Database Browser (SBDB)
        name => name of the object

        Note that the above ID is the identifier of the object in the
        SBDB, not in JPL Horizons. You can supply the ID value to
        jplObjectDBSearch as the targetID and the return value will be
        the identifier of the object in the JPL Horizons system.
    
    Raises:
        MissingInputError
    """

    if targetName:
        jplHorizonsMB = searchJplHorizonsMB(targetName)
        if jplHorizonsMB:
            targetID = jplHorizonsMB
        else:
            jplSmallBodyDBOutput = jplSmallBodyDBQuery(jplSmallBodyDBurl, sstr=targetName)
            targetID = parseJPLSmallBodyDBOutput(jplSmallBodyDBOutput)
    elif targetID:
        jplSmallBodyDBOutput = jplSmallBodyDBQuery(jplSmallBodyDBurl, ID=targetID)
        targetID = parseJPLSmallBodyDBOutput(jplSmallBodyDBOutput)
    else:
        raise MissingInputError('You must supply either a target name or a target ID')
    logger.info('DB search result %s' % targetID)
    return targetID

def main(options, args):
    # Create top level logger.
    logger = ssdlog.make_logger('jplObjectDBSearch', options)
    
    targetID = jplObjectDBSearch(options.targetName, options.targetID, logger)
    logger.info('targetID %s' % targetID)
    print 'targetID %s' % targetID

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
    optprs.add_option("-t", dest="targetName", default=None,
                      help="Target name")
    optprs.add_option("-i", dest="targetID", default=None,
                      help="Target ID")

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

