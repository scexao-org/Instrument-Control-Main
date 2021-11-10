import re
import tempfile
import os.path

UNTITLED = 'Untitled'

class List(list):
  def __init__(self,*args):
    super(List,self).__init__(*args)
#  def __repr__(self):
#    return("%s=%s" %(self.name,super(List,self).__repr__()))


def ReadPlanFile(filename):
  infile = open(filename,"r")
  instr = infile.read()
  local_dict = {}
  global_dict = {}
  exec instr in global_dict,local_dict
  return(local_dict['myplan'])
#

def WritePlanFile(filename,plan):
  (outname,outext) = os.path.splitext(os.path.basename(filename))
  (tmphandle, tmpfilename) = tempfile.mkstemp('.spot',outname+'_')
  out = open(filename,"w")
  out.write(repr(plan))
  out.close()
  # This is the best I can do for undo right now.
  # I could keep a list of these.
  tmp = open(tmpfilename,"w")
  tmp.write(repr(plan))
  tmp.close()
#

class Plan(object):
  POUND_BANG_LINE = "#!/usr/bin/env python\n"
  MACHINE_GENERATED_WARNING = '''
#################################
#
#  WARNING!  WARNING!  WARNING!
#  This file was created by SPOT, The Subaru Planning and Observation Tool
#  You should not edit this file.  You should use SPOT to make changes.
#
#################################
'''
  TARGET_ASSIGN_HDR = "### Target Assignments ###\n\n"
  TARGET_ASSIGN_STR = "target_autogen_%03d = %s\n\n"
  TARGET_ASSIGN_FTR = "### end of Target ###\n\n"
  TARGET_LIST_ASSIGN_HDR = "# List of Target Assignments\ntargetList = [\n"
  TARGET_LIST_ASSIGN_STR = "  target_autogen_%03d,\n"
  TARGET_LIST_ASSIGN_FTR = "]  # end of targetList[]\n"

  TELCONFIG_ASSIGN_HDR = "### TelConfig Assignments ###\n\n"
  TELCONFIG_ASSIGN_STR = "telConfig_autogen_%03d = %s\n\n"
  TELCONFIG_ASSIGN_FTR = "### end of TelConfig Assignments ###\n\n"
  TELCONFIG_LIST_ASSIGN_HDR = "# List of TelConfig Assignments\ntelConfigList = [\n"
  TELCONFIG_LIST_ASSIGN_STR = "  telConfig_autogen_%03d,\n"
  TELCONFIG_LIST_ASSIGN_FTR = "]  # end of telConfigList[]\n"

  INSTCONFIG_ASSIGN_HDR = "### InstConfig Assignments ###\n\n"
  INSTCONFIG_ASSIGN_STR = "instConfig_autogen_%03d = %s\n\n"
  INSTCONFIG_ASSIGN_FTR = "### end of instConfig Assignments ###\n\n"
  INSTCONFIG_LIST_ASSIGN_HDR = "# List of InstConfig Assignments\ninstConfigList = [\n"
  INSTCONFIG_LIST_ASSIGN_STR = "  instConfig_autogen_%03d,\n"
  INSTCONFIG_LIST_ASSIGN_FTR = "]  # end of instConfigList[]\n"

  DITHER_ASSIGN_HDR = "### Dither Assignments ###\n\n"
  DITHER_ASSIGN_STR = "dither_autogen_%03d = %s\n\n"
  DITHER_ASSIGN_FTR = "### end of Dither Assignments ###\n\n"
  DITHER_LIST_ASSIGN_HDR = "# List of Dither Assignments\nditherList = [\n"
  DITHER_LIST_ASSIGN_STR = "  dither_autogen_%03d,\n"
  DITHER_LIST_ASSIGN_FTR = "]  # end of ditherList[]\n"

  ACTIVITY_ASSIGN_HDR = "### Activity Assignments ###\n\n"
  ACTIVITY_ASSIGN_STR = """activity_autogen_%03d = comics.Activity(\
target_autogen_%03d,
  telConfig_autogen_%03d, instConfig_autogen_%03d, dither_autogen_%03d,
  comment=%r,
  tag=%r,status=%r)\n\n"""
  ACTIVITY_ASSIGN_FTR = "### end of Activity Assignments ###\n\n"
  ACTIVITY_LIST_ASSIGN_HDR = "# List of Activity Assignments\nactivityList = [\n"
  ACTIVITY_LIST_ASSIGN_STR = "  activity_autogen_%03d,\n"
  ACTIVITY_LIST_ASSIGN_FTR = "]  # end of activityList[]\n"

  PLAN_EXTEND_TARGETS_STR = "myplan.targets.extend(targetList)\n"
  PLAN_EXTEND_TELCONFIGS_STR = "myplan.telConfigs.extend(telConfigList)\n"
  PLAN_EXTEND_INSTCONFIGS_STR = "myplan.instConfigs.extend(instConfigList)\n"
  PLAN_EXTEND_DITHERS_STR = "myplan.dithers.extend(ditherList)\n"
  PLAN_EXTEND_ACTIVITIES_STR = "myplan.activities.extend(activityList)\n"

  PLAN_FILE_FOOTER = """
### end of file
"""

  def __init__(self,name=UNTITLED):
    self.name = name
    self.oAcct = ""
    self.comment = Comment()
    self.targets = List()
    self.telConfigs = List()
    self.instConfigs = List()
    self.dithers = List()
    self.activities = List()

  def makeTargetAssignments(self):
    st  = Plan.TARGET_ASSIGN_HDR
    for i,target in enumerate(self.targets):
      st += Plan.TARGET_ASSIGN_STR % (i,repr(target))
    st  += Plan.TARGET_ASSIGN_FTR
    return(st)
  #
  def makeListOfTargetAssignments(self):
    st  = Plan.TARGET_LIST_ASSIGN_HDR
    for i,target in enumerate(self.targets):
      st += Plan.TARGET_LIST_ASSIGN_STR % (i)
    st += Plan.TARGET_LIST_ASSIGN_FTR
    return(st)
  #

  def makeTelConfigAssignments(self):
    st  = Plan.TELCONFIG_ASSIGN_HDR
    for i,telConfig in enumerate(self.telConfigs):
      st += Plan.TELCONFIG_ASSIGN_STR % (i,repr(self.telConfigs[i]))
    st  += Plan.TELCONFIG_ASSIGN_FTR
    return(st)
  #
  def makeListOfTelConfigAssignments(self):
    st  = Plan.TELCONFIG_LIST_ASSIGN_HDR
    for i,telConfig in enumerate(self.telConfigs):
      st += Plan.TELCONFIG_LIST_ASSIGN_STR % (i)
    st += Plan.TELCONFIG_LIST_ASSIGN_FTR
    return(st)
  #

  def makeInstConfigAssignments(self):
    st  = Plan.INSTCONFIG_ASSIGN_HDR
    for i,instConfig in enumerate(self.instConfigs):
      st += Plan.INSTCONFIG_ASSIGN_STR % (i,repr(self.instConfigs[i]))
    st  += Plan.INSTCONFIG_ASSIGN_FTR
    return(st)
  #
  def makeListOfInstConfigAssignments(self):
    st  = Plan.INSTCONFIG_LIST_ASSIGN_HDR
    for i,instConfig in enumerate(self.instConfigs):
      st += Plan.INSTCONFIG_LIST_ASSIGN_STR % (i)
    st += Plan.INSTCONFIG_LIST_ASSIGN_FTR
    return(st)
  #

  def makeDitherAssignments(self):
    st  = Plan.DITHER_ASSIGN_HDR
    for i,dither in enumerate(self.dithers):
      st += Plan.DITHER_ASSIGN_STR % (i,repr(self.dithers[i]))
    st  += Plan.DITHER_ASSIGN_FTR
    return(st)
  #
  def makeListOfDitherAssignments(self):
    st  = Plan.DITHER_LIST_ASSIGN_HDR
    for i,dither in enumerate(self.dithers):
      st += Plan.DITHER_LIST_ASSIGN_STR % (i)
    st += Plan.DITHER_LIST_ASSIGN_FTR
    return(st)
  #

  def makeActivityAssignments(self):
    st  = Plan.ACTIVITY_ASSIGN_HDR
    for i,activity in enumerate(self.activities):
      st += Plan.ACTIVITY_ASSIGN_STR % (i,
                     self.targets.index(self.activities[i].target),
                     self.telConfigs.index(self.activities[i].telConfig),
                     self.instConfigs.index(self.activities[i].instConfig),
                     self.dithers.index(self.activities[i].dither),
                     self.activities[i].comment,self.activities[i].tag,
                     self.activities[i].status
                     )
    st  += Plan.ACTIVITY_ASSIGN_FTR
    return(st)
  #
  def makeListOfActivityAssignments(self):
    st  = Plan.ACTIVITY_LIST_ASSIGN_HDR
    for i,activity in enumerate(self.activities):
      st += Plan.ACTIVITY_LIST_ASSIGN_STR % (i)
    st += Plan.ACTIVITY_LIST_ASSIGN_FTR
    return(st)
  #


  def __str__(self):
    return("Plan(\n  name=%s\n  targets=%s\n  telConfigs=%s\n  instConfigs=%s\n\
dithers=%s\n  activities=%s,comment=\"\"\"%s\"\"\",status=\"\"\"%s\"\"\",\
tag=\"\"\"%s\"\"\")"%(self.name,self.targets,self.telConfigs,
           self.instConfigs,self.dithers,self.activities,
           self.comment,self.tag,self.status))
  def __repr__(self):
    st = ""
    st += Plan.POUND_BANG_LINE
    st += Plan.MACHINE_GENERATED_WARNING
    st += "\n"
    st += "import plan\n"
    st += "import comics\n"
    st += "\n"
    st += "#\n"
    st += "# Plan: %s\n" % str(self.name)
    st += "#       %s\n" % str(self.comment)
    st += "#\n"
    st += "\n"
    st += "myplan = plan.Plan(%r)\n" % (self.name,)
    st += "\n"
    st += "myplan.comment = plan.Comment(%r)\n" % (self.comment,)
    st += "myplan.oAcct = %r\n" % (self.oAcct,)
    st += "\n"
    st += "\n"
    st += "%s\n" % self.makeTargetAssignments()
    st += "\n"
    st += "%s\n" % self.makeTelConfigAssignments()
    st += "\n"
    st += "%s\n" % self.makeInstConfigAssignments()
    st += "\n"
    st += "%s\n" % self.makeDitherAssignments()
    st += "\n"
    st += "%s\n" % self.makeActivityAssignments()
    st += "\n"
    st += "%s\n" % self.makeListOfTargetAssignments()
    st += "\n"
    st += "%s\n" % self.makeListOfTelConfigAssignments()
    st += "\n"
    st += "%s\n" % self.makeListOfInstConfigAssignments()
    st += "\n"
    st += "%s\n" % self.makeListOfDitherAssignments()
    st += "\n"
    st += "%s\n" % self.makeListOfActivityAssignments()
    st += "\n"
    st +=  Plan.PLAN_EXTEND_TARGETS_STR
    st +=  Plan.PLAN_EXTEND_TELCONFIGS_STR
    st +=  Plan.PLAN_EXTEND_INSTCONFIGS_STR
    st +=  Plan.PLAN_EXTEND_DITHERS_STR
    st +=  Plan.PLAN_EXTEND_ACTIVITIES_STR
    st +=  Plan.PLAN_FILE_FOOTER

    return(st)

class Comment:
  def __init__(self,text=""):
    self.text = text
  def __str__(self):
    return(self.text)
  def __repr__(self):
    return('%r' % self.text)


class Target:
  TARGET_EQUINOX_STRS = ('J2000', 'B1950')
  TARGET_EQUINOX = dict(zip(TARGET_EQUINOX_STRS,range(len(TARGET_EQUINOX_STRS))))

  TARGET_STYLE_STRS = ('OBJECT','STANDARD')
  TARGET_STYLE = dict(zip(TARGET_STYLE_STRS,range(len(TARGET_STYLE_STRS))))

  DEF_STYLE = 'OBJECT'
  DEF_RA =  '00:00:00.000'
  DEF_DEC = '+00:00:00.00'
  DEF_EQUINOX = 'J2000'
  RE_RA_PATTERN  = re.compile( '(\d+?)\:(\d+?)\:(\d+\.?\d*$)' )
  RE_DEC_PATTERN = re.compile( '([+-]?\d+?)\:(\d+?)\:(\d+\.?\d*$)' )

  def __init__(self,name=UNTITLED,ra=DEF_RA,dec=DEF_DEC,equinox=DEF_EQUINOX
                                                           ,style=DEF_STYLE):
    self.name = name
    self.style = style
    if style == None:
      self.style = Target.DEF_STYLE
    self.ra = ra
    self.dec = dec
    self.equinox = equinox
    self.VALIDATE_METHODS = { 'ra':    self.isRaValid, 
                              'dec':   self.isDecValid }

  def isRaValid(self):
    try:
      mobj = Target.RE_RA_PATTERN.match( self.ra )     # get match object
    except:
      return '"%s" is not a valid RA string' % self.ra
    if  mobj:
      #? print 'mobj groups 1,2,3 = "%s", "%s", "%s"' % \
      #?       ( mobj.group(1), mobj.group(2), mobj.group(3) )
      hr  = int(   mobj.group(1) )
      min = int(   mobj.group(2) )
      sec = float( mobj.group(3) )
      ok = True
      if hr > 23:
        ok = False
      if min > 59:
        ok = False
      if sec > 59:
        ok = False
      if  not ok:
        return '%02d:%02d:%06.3f is not a valid RA value' % (hr,min,sec)
    else:
      return '"%s" is not a valid RA string' % self.ra
    #
    return True     # should NEVER get here!
    
  def isDecValid(self):
    try:
      mobj = Target.RE_DEC_PATTERN.match( self.dec )     # get match object
    except:
      return '"%s" is not a valid DEC string' % self.dec
    if  mobj:
      deg = int(   mobj.group(1) )
      min = int(   mobj.group(2) )
      sec = float( mobj.group(3) )
      ok = True
      if deg > 89:
        ok = False
      if min > 59:
        ok = False
      if sec > 59:
        ok = False
      if  not ok:
        return '%02d:%02d:%05.2f is not a valid DEC value' % (deg,min,sec)
    else:
      return '"%s" is not a valid DEC string' % self.dec
    #
    return True     # should NEVER get here!


  def isValid( self, elementList=('ra','dec') ):
    retDict = {}
    ret = True
    for  elem in elementList:
        res = self.VALIDATE_METHODS[elem]()
        if  res != True:
            retDict[elem] = res
            ret = False
    #? print "isValid ret, retDict = %s : %s\n" % (`ret`,`retDict`)
    if  ret:
        return ret
    else:
        return retDict
    
  def __str__(self):
    return("Target(name=%s,ra=%s,dec=%s)"%(self.name,self.ra,self.dec))
  def __repr__(self):
    return("plan.Target(name=%r,\n  ra=%r, dec=%r, equinox=%r, style=%r)"%(
            self.name,self.ra,self.dec,self.equinox,self.style))

