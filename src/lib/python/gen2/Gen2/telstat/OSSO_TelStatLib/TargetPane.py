# TargetPane.py -- Takeshi Inagaki, Bruce Bon, et al -- 2006-12-22
#
# This TargetPane displays following data:
#                                        Proposal ID
#                                        Object
#                                        Airmass
#                                        Time to Limit
#                                        PA

#! /usr/local/bin/python

title = 'TargetPane'

import os
import sys
import Util         
import time

import TelStatLog
from Tkinter import *
from Tkconstants import *
from TelStat_cfg import *
from StatIO import *
from DispType import *
from AudioPlayer import *
from Alert import *


# TSCL.LIMIT_FLAG values:
LIM_FLAG_EL_LOW  = 0x01
LIM_FLAG_EL_HIGH = 0x02
LIM_FLAG_AZ      = 0x04
LIM_FLAG_ROT     = 0x08
LIM_FLAG_BIGROT  = 0x10


class TargetPane (Frame, StatPaneBase):
    def __init__(self, parent,  pfgcolor=TARGETPANEFOREGROUND, pbgcolor=TARGETPANEBACKGROUND):

        # Create a frame to put the LabeledWidgets into
        Frame.__init__(self,parent)
        StatPaneBase.__init__(self, ( 'TELSTAT.UNIXTIME', 
                'FITS.SBR.MAINOBCP', 'TSCS.EL',
                'TSCL.LIMIT_EL_LOW', 'TSCL.LIMIT_EL_HIGH',
                'TSCL.LIMIT_AZ', 'TSCL.LIMIT_ROT', 'TSCV.PROBE_LINK',
                'TSCL.InsRotPA', 'TSCL.ImgRotPA',  'TSCL.INSROTPA_PF', 
                'STATS.ROTDIF',  'STATS.ROTDIF_PF', 'TELSTAT.TELDRIVE',
                'TELSTAT.M1_CLOSED', 'TELSTAT.DOME_CLOSED', 'TELSTAT.FOCUS',
                'TELSTAT.ROTATOR', 'TELSTAT.EL_STOWED', 'TELSTAT.SLEWING'), 
                'TargetPane')
#       self.pack(fill = 'both', expand = 1)
        self.configure(bg=pbgcolor[0])
        self.azLimAlert  = AudioAlert( 
                        warnAudio=AU_WARN_AZ_LIMIT_TIME, warnMinInterval=300, 
                        alarmAudio=AU_ALARM_AZ_LIMIT_TIME, alarmMinInterval=10 )
        self.elLimAlert  = AudioAlert( 
                        warnAudio=AU_WARN_EL_LIMIT_TIME, warnMinInterval=300, 
                        alarmAudio=AU_ALARM_EL_LIMIT_TIME, alarmMinInterval=10 )
        self.rotLimAlert = AudioAlert( 
                        warnAudio=AU_WARN_ROT_LIMIT_TIME, warnMinInterval=300, 
                        alarmAudio=AU_ALARM_ROT_LIMIT_TIME,alarmMinInterval=10 )
        self.paCmdAlert = AudioAlert( 
                        warnAudio=AU_WARN_PA_CMDFAIL, warnMinInterval=300, 
                        alarmAudio=None )

        # Initialize instrument and instrument-dependent aliases to None for unknown    
        self.instrument = self.propIDalias = self.objAlias = None

        # Create proposal ID label
        self.proposal = Label(self,  text = 'Proposal ID',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.proposal.configure(relief='solid', borderwidth=0)
        self.proposal.grid(column=0, row=0, padx=12, sticky = 'w')

        # Proposal id  
        self.idValue  = Label(self, text = '<No Data>',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.idValue.configure(relief='solid', borderwidth=0)
        self.idValue.grid(column=1, row=0, padx=8, sticky="w")
                
        # Create object label
        self.object = Label(self,  text = 'Object',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.object.configure(relief='solid', borderwidth=0)
        self.object.grid(column=0, row=1, padx=12, sticky = 'w')

        # Object value  
        self.oValue  = Label(self, text = ' ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.oValue.configure(relief='solid', borderwidth=0)
        self.oValue.grid(column=1, row=1, padx=8, sticky ='w')

        # Create airmass label
        self.airmass = Label(self, text = 'Air Mass',  font=fontBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.airmass.configure(relief='solid', borderwidth=0)
        self.airmass.grid(column=0, row=2, padx=12, sticky = 'W')

        # Airmass value
        self.aValue  = Label(self, text = ' ',  font=fontBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.aValue.configure(relief='solid', borderwidth=0)
        self.aValue.grid(column=1, row=2, padx=8, sticky ='w')

        # Create PA label
        self.pa = Label(self, text = 'Position Angle',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.pa.configure(relief='solid', borderwidth=0)
        self.pa.grid(column=0, row=4, padx=12, sticky ='w')

        # PA value
        self.pValue  = Label(self, text = 'deg TEST',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.pValue.configure(relief='solid', borderwidth=0)
        self.pValue.grid(column=1, row=4, padx=8, sticky ='w')

        
        # Create elevation limit label
        self.limit = Label(self, text = 'Time to Elev Limit ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.limit.configure(relief='solid', borderwidth=0)
        self.limit.grid(column=0, row=5, padx=12, sticky ='w')

        # Elevation Limit value
        self.el_lValue  = Label(self, text = ' ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.el_lValue.configure(relief='solid', borderwidth=0)
        self.el_lValue.grid(column=1, row=5, padx=8, sticky ='w')

        #-----vvvvvvv--------------
        # Create rotator limit label
        self.limit2 = Label(self, text = 'Time to Rot Limit ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.limit2.configure(relief='solid', borderwidth=0)
        self.limit2.grid(column=0, row=6, padx=12, sticky ='w')

        # Rotator Limit value
        self.rot_lValue  = Label(self, text = ' ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.rot_lValue.configure(relief='solid', borderwidth=0)
        self.rot_lValue.grid(column=1, row=6, padx=8, sticky ='w')
        
        
        
        # Create azimuth limit label
        self.limit3 = Label(self, text = 'Time to Az Limit ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0])
        self.limit3.configure(relief='solid', borderwidth=0)
        self.limit3.grid(column=0, row=7, padx=12, sticky ='w')

        # Azimuth Limit value
        self.az_lValue  = Label(self, text = ' ',  font=fontSmallBold, bg=pbgcolor[0], fg=pfgcolor[0], width=28, anchor='w')
        self.az_lValue.configure(relief='solid', borderwidth=0)
        self.az_lValue.grid(column=1, row=7, padx=8, sticky ='w')
        #-----^^^^^^--------------
        
          # initialize
        self.focus      = None
        self.PAdiffHigh = False
        self.PAcmdTime  = 0.0
        self.secPerDeg  = 0.0
        self.secSuppression = 0.0
   

    # Set active flag for a dictionary entry
    def __setActiveFlag(self,dict,key,flag):
        """Set the active flag for a status dictionary entry and force the
        entry's value to None if it is inactive."""
        #? print "Turning %s to %s" % (`key`,`flag`)
        try:
            dict[key].setActive( flag )
            if  not flag:
                dict[key].setValue( None )   # force inactive values to None
        except:
            TelStatLog.TelStatLog( TelStat_cfg.TargErrBase,
                "TargetPane.__setActiveFlag():  error during dictionary assignment." )

    # Update values
    def update(self,dict, pbgcolor=TARGETPANEBACKGROUND, pfgcolor=TARGETPANEFOREGROUND):

        # Find instrument and turn on its status alias dictionary entries
        instrument = dict['FITS.SBR.MAINOBCP'].value()
        self.prevFocus = self.focus
        self.focus     = dict['TELSTAT.FOCUS'].value()
        if  instrument == None:
            propIDalias = objAlias = None
        else: # instrument != None
            instrument = instrument.strip()
            if  OBCPSYM.has_key( instrument ):
                aName = OBCPSYM.get( instrument, 'NONE' ) # should never get NONE
                propIDalias = 'FITS.' + aName + '.PROP_ID'
                objAlias = 'FITS.' + aName + '.OBJECT'
            else:
                TelStatLog.TelStatLog( TelStat_cfg.TargErrBase,
                    'TargetPane.update():  instrument %s not found.' % \
                    `instrument` )
                instrument = propIDalias = objAlias = None
        if  self.instrument != instrument:
            if  self.propIDalias != None:
                self.__setActiveFlag( dict, self.propIDalias, False )
            self.propIDalias = propIDalias
            if  self.propIDalias != None:
                self.__setActiveFlag( dict, self.propIDalias, True )
            if  self.objAlias != None:
                self.__setActiveFlag( dict, self.objAlias, False )
            self.objAlias = objAlias
            if  self.objAlias != None:
                self.__setActiveFlag( dict, self.objAlias, True )
            self.instrument = instrument

        # Proposal ID value
        propIDstr = '<No Data>'
        if  propIDalias != None:
            try:
                propIDstr = dict[propIDalias].format()
            except:
                TelStatLog.TelStatLog( TelStat_cfg.TargErrBase,
                    "TargetPane.update():  alias %s not found." % `propIDalias` )
                propIDstr = '%s unknown alias' % `propIDalias`
        self.idValue.configure( text = propIDstr )

        # Object value
        objStr = '<No Data>'
        if  objAlias != None:
            try:
                objStr = dict[objAlias].format()
            except:
                TelStatLog.TelStatLog( TelStat_cfg.TargErrBase,
                    "TargetPane.update():  alias %s not found." % `objAlias` )
                objStr = '%s unknown alias' % `objAlias`
        self.oValue.configure( text = objStr )

        # Airmass value, and determine whether to sound audio alert for lim time
        el = dict['TSCS.EL'].value_ArcDeg()
        if  el == None:
            self.aValue.configure(text = '<No Data>')
        else:
            airmassData = Util.calcAirMass(el)
            if  airmassData == None:
                self.aValue.configure(text = '<No Data>')
            else:
                self.aValue.configure(text = ('%.2f' % airmassData))

        # Determine whether to sound audio alert for limit time.
        # The conditions used here are computed by the GlobalStates.py module.
        # Any of them are taken to mean that the telescope is currently 
        # inactive and that any limit alert condition may be a consequence of
        # data that is not meaningful when the telescope is inactive.
        if  dict['TELSTAT.M1_CLOSED'].value() or     \
            dict['TELSTAT.DOME_CLOSED'].value() or   \
            dict['TELSTAT.EL_STOWED'].value() or     \
            dict['TELSTAT.SLEWING'].value() or       \
            dict['TELSTAT.TELDRIVE'].value() == TelStat_cfg.TELDRIVE_POINT:
            SoundLimAlert = False
        else:
            SoundLimAlert = True

        #? SoundLimAlert = True    # for testing only ????????

        # Limit EL_LOW value
        limitEL_LOW = dict['TSCL.LIMIT_EL_LOW']
        limitEL_LOWmin = limitEL_LOW.value_Min()        # in hrmin

        # Limit EL_HIGH value
        limitEL_HIGH = dict['TSCL.LIMIT_EL_HIGH']
        limitEL_HIGHmin = limitEL_HIGH.value_Min()      # in hrmin

        # Limit AZ value
        limitAZ = dict['TSCL.LIMIT_AZ']
        limitAZmin = limitAZ.value_Min()                # in hrmin

        # Limit Rotator value
        limitROT = dict['TSCL.LIMIT_ROT']
        limitROTmin = limitROT.value_Min()              # in hrmin
            
        # Limit flag value
        limitFlag = dict['TSCL.LIMIT_FLAG'].value()

        # Figure out lowest limit and symbol(s) to display
        limitMin = 721                          # > max value in minutes
        limitSym = ""
        limitingValue = None
        # this will get the lower limit of EL_LOW & EL_HIGH
        limit_el_high_low = None
        
        if  limitFlag != None:
            if  limitFlag & LIM_FLAG_EL_LOW:
                if  limitEL_LOWmin != None:
                    #print "-------"
                    #print "lim el low min: %d" % (limitEL_LOWmin)
                    if  limitEL_LOWmin < limitMin:
                        limitMin = limitEL_LOWmin
                        limitSym = " <-Limit EL (Low)"
                        limitAlert = self.elLimAlert
                        limit = limitEL_LOW
                        limitingValue = self.el_lValue
                        limit_el_high_low = limitEL_LOW
            if  limitFlag & LIM_FLAG_EL_HIGH:
                if  limitEL_HIGHmin != None:
                    #print "lim el high min: %d" % (limitEL_HIGHmin)
                    if  limitEL_HIGHmin < limitMin:
                        limitMin = limitEL_HIGHmin
                        limitSym = " <-Limit EL (High)"
                        limitAlert = self.elLimAlert
                        limit = limitEL_HIGH
                        limitingValue = self.el_lValue
                        limit_el_high_low = limitEL_HIGH
            if  limitFlag & LIM_FLAG_AZ:
                if  limitAZmin != None:
                    #print "lim az min: %d" % (limitAZmin)
                    if  limitAZmin < limitMin:
                        limitMin = limitAZmin
                        limitSym = " <-Limit Az"
                        limitAlert = self.azLimAlert
                        limit = limitAZ
                        limitingValue = self.az_lValue
                else:
                    #print "limitAZmin == None"
                    pass
            else:
                #print "LIM_FLAG_AZ not set"
                pass

            notbigrot = not( limitFlag & LIM_FLAG_BIGROT )
                # If LIM_FLAG_BIGROT bit is set, Rotator time-to-limit 
                # is at least 720 minutes -> no alert
            if  notbigrot and (limitFlag & LIM_FLAG_ROT):
                # focus value, and is it a non-prime-focus
                #print "notbigrot and (limitFlag & LIM_FLAG_ROT)"
                focusNotPrime = False
                if  self.focus != None and self.focus != UNDEF and \
                    self.focus != FOCUS_PF_OPT and self.focus != FOCUS_PF_IR and self.focus != FOCUS_PF_OPT2:
                    focusNotPrime = True
                # probe_link value
                probeLink = dict['TSCV.PROBE_LINK'].value()
                # find symbol "Rotator" or "Probe"
                if  probeLink == None:
                    sym = "limit: Unknown"
                elif  (probeLink & 0x01) == 0x01 and focusNotPrime:
                    sym = " <-Limit Probe"
                else:
                    sym = " <-Limit Rotator"
                # is this minimum or not
                if  limitROTmin != None:
                    #  ???? Temporary replacement line because of flaky TSCL.LIMIT_ROT ????
                    #  ????     if  limitROTmin != 0.0 and limitROTmin < limitMin:
                    #print "lim rot min: %d" % (limitROTmin)
                    if  limitROTmin < limitMin:
                        limitMin = limitROTmin
                        limitSym = sym
                        limitAlert = self.rotLimAlert
                        limit = limitROT
                        limitingValue = self.rot_lValue
                else:
                    #print "limitROTmin == None"
                    pass
            else:
                #print "!(notbigrot and (limitFlag & LIM_FLAG_ROT))"
                pass

        # No limit data
        if limitFlag == None:
            self.el_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])
            self.rot_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])
            self.az_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])

        # fixme: what about a case like these?
        #elif  limitEL_LOWmin == None or limitEL_HIGHmin == None or        \
        #      limitAZmin == None or limitROTmin == None:
        #    self.el_lValue.configure(text = ('<Missing Data>'), 
        #                          bg = pbgcolor[0], fg=pfgcolor[0])

        
        # no problem, limits long time away
        elif  limitMin > 720.0:
            self.el_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])
            self.rot_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])
            self.az_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])
        # we have limit info to display, maybe warn
        else:
            if limitMin <= 30  and limitMin > 1:
                limitingValue.configure(text = ('%s <= 30m%s' %  \
                    (limit.format_HM(1), limitSym)), bg = pbgcolor[1], fg=pfgcolor[1])
                if SoundLimAlert:
                    limitAlert.setMinIntervals( warnMinInterval=limitMin*20 )
                    limitAlert.alert()  # repeat warning in 1/3 of limitMin (in sec)
            elif limitMin <= 1:
                limitingValue.configure(text = ('%s <= 1m%s' %           \
                    (limit.format_HM(1), limitSym)), bg = pbgcolor[2], fg=pfgcolor[0])
                if SoundLimAlert:
                    limitAlert.alert( level = ALARM )
                                # repeat alarm as initialized in limitAlert (10 sec)
            else:
                limitingValue.configure(text = ('%s %s' %         \
                    (limit.format_HM(1), limitSym)), bg = pbgcolor[0], fg=pfgcolor[0])

            # also update the non limiting values
            if self.el_lValue != limitingValue:
                if ((limitFlag & LIM_FLAG_EL_LOW) or (limitFlag & LIM_FLAG_EL_HIGH)):
                    if limit_el_high_low != None:
                        self.el_lValue.configure(text = limit_el_high_low.format_HM(1), 
                                                     bg = pbgcolor[0], fg=pfgcolor[0])
                    else:
                        self.el_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])
                else:
                    self.el_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])

            if self.rot_lValue != limitingValue:
                if (notbigrot and (limitFlag & LIM_FLAG_ROT)):
                    if limitROTmin != None:
                        self.rot_lValue.configure(text = limitROT.format_HM(1), 
                                                     bg = pbgcolor[0], fg=pfgcolor[0])
                    else:
                        self.rot_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])
                else:
                    self.rot_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])
            
            if self.az_lValue != limitingValue:
                if (limitFlag & LIM_FLAG_AZ):
                    if limitAZmin != None:
                        self.az_lValue.configure(text = limitAZ.format_HM(1), 
                                                     bg = pbgcolor[0], fg=pfgcolor[0])
                    else:
                        self.az_lValue.configure(text = ('<Missing Data>'), bg = pbgcolor[0], fg=pfgcolor[0])
                else:
                    self.az_lValue.configure(text = ('--h --m'), bg = pbgcolor[0], fg=pfgcolor[0])
            
        # Determine whether to sound audio alert for PA anomaly.
        # The conditions used here are computed by the GlobalStates.py module.
        # The first three of them are taken to mean that the telescope is 
        # currently inactive and that any limit alert condition may be a 
        # consequence of data that is not meaningful when the telescope is 
        # inactive.  The fourth one indicates that the rotator is off,
        # so the position angle cannot be controlled.  The last one means 
        # that the telescope is in the midst of a slew, during which it is 
        # normal that the actual PA will be  different from the commanded PA.
        if  dict['TELSTAT.M1_CLOSED'].value() or     \
            dict['TELSTAT.DOME_CLOSED'].value() or   \
            dict['TELSTAT.EL_STOWED'].value() or     \
            dict['TELSTAT.ROTATOR'].value() == ROT_OUT or     \
            dict['TELSTAT.SLEWING'].value():
            SoundRotAlert = False
        else:
            SoundRotAlert = True

        # PA value - select values and compute as needed
            # get current time
        t = dict['TELSTAT.UNIXTIME'].value()
            # get focus and see if it has changed
        if  self.focus != None and self.prevFocus != self.focus:
            self.PAcmdTime  = t

            # get cmdDiff
        if  self.focus == FOCUS_PF_OPT or self.focus == FOCUS_PF_IR or self.focus == FOCUS_PF_OPT2:#prime focus
            cmdDiff = dict['STATS.ROTDIF_PF'].value_ArcDeg()
        else:                                                  # focus Cs or Ns
            cmdDiff = dict['STATS.ROTDIF'].value_ArcDeg()

            # get position angle and force it into normal range
        if  self.focus == FOCUS_PF_OPT or self.focus == FOCUS_PF_IR or self.focus == FOCUS_PF_OPT2:#prime focus
            rawPosAng = dict['TSCL.INSROTPA_PF'].value_ArcDeg()
            self.secPerDeg  = TARGETPANESECPERDEG_PF
        elif  self.focus == FOCUS_CS_OPT or self.focus == FOCUS_CS_IR:
                                                              # Cassegrain focus
            rawPosAng = dict['TSCL.InsRotPA'].value_ArcDeg()      
            self.secPerDeg  = TARGETPANESECPERDEG_CS
        elif  self.focus == FOCUS_NS_OPT or self.focus == FOCUS_NS_IR:
                                                                 # Nasmyth focus
            rawPosAng = dict['TSCL.ImgRotPA'].value_ArcDeg()      
            self.secPerDeg  = TARGETPANESECPERDEG_NS
        else:           # focus unknown ==> display "No Data" and return
            self.pValue.configure(text = '<No Data>', bg = pbgcolor[0], fg=pfgcolor[2])
            return
        if  rawPosAng == None:
            posAngle = None
        else:
            posAngle = ((rawPosAng + 540.0) % 360.0) - 180.0

        # PA value - display
        if  cmdDiff == None or posAngle == None: # ==> display "No Data", return
            self.pValue.configure(text = '<No Data>', bg = pbgcolor[0], fg=pfgcolor[2])
            return
          # depending on status, background color will be changed
        if  SoundRotAlert and cmdDiff >= 0.1:
            # set up for suppression when cmdDiff first goes high
            if  not self.PAdiffHigh:
                self.PAcmdTime  = t
                self.secSuppression = 6.0 + self.secPerDeg * cmdDiff
                # ??? Following log should be removed in some future version ???
                TelStatLog.TelStatLog( TelStat_cfg.TargInfoBase,
                    ('TargetPane.update():  position angle deflection of %.1f' +
                        ' degrees, audio suppressed for %.1f seconds.') % \
                    (cmdDiff, self.secSuppression) )
            # display the high value with colored background
            self.pValue.configure(
                      text = ('%.2f deg, diff=%.2f>=0.1' % (posAngle,cmdDiff)),
                      bg = pbgcolor[1], fg=pfgcolor[1])
            # suppress if slewing or inactive, 
            #   and for secSuppression sec after transition
            if  SoundRotAlert and (t - self.PAcmdTime > self.secSuppression):
                self.secSuppression = 0.0   # suppress only once for delay
                self.paCmdAlert.alert()   # rotator commanded position not achieved
            self.PAdiffHigh = True
        else:  # cmdDiff < 0.1 or not SoundRotAlert
            # display the normal value with normal background
            self.pValue.configure(text = ('%.2f deg' % posAngle), bg = pbgcolor[0], fg=pfgcolor[2])
            self.PAdiffHigh = False
       
    # Update the label every second.
    def tick(self):
        self.update()
        self.after(1000, self.tick)

    def refresh(self,dict):
        self.update(dict, TARGETPANEBACKGROUND,  TARGETPANEFOREGROUND)

        
    def rePack(self):
        pass
    
