#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2006-12-04 16:28 Bruce Bon

#  This module implements the environment status display pane.

from Tkinter import *      # UI widgets and event loop infrastructure
from StatIO import *       # Status I/O functions
from DispType import *     # Status display data types
from TelStatLog import *   # Log infrastructure
from TelStat_cfg import *  # Display configuration
from Alert import *        # Alert infrastructure
import Pmw                 # Additional UI widgets 
import LineGraph           # Strip chart widgets
import time                # System time functions

class EnvPane(Frame, StatPaneBase):
    def __init__(self, parent, pbgcolor=ENVPANEBACKGROUND):
        """Create an instance of the environment status display pane."""
        # Configure the frame so that its boundary can be seen
        Frame.__init__(self, parent, borderwidth=paneBorderWidth, relief=paneBorderRelief)

        # The environment pane consists of 3 strip charts showing temperature, humidity
        # and wind speed both at the summit and inside the observatory dome.
        # Register the status symbols that we want to receive.
        StatPaneBase.__init__(self, 
            ('TELSTAT.UNIXTIME','TELSTAT.DOME_CLOSED','TSCL.TEMP_O','TSCL.TEMP_I','TSCL.HUMI_O',
            'TSCL.HUMI_I','TSCL.WINDS_O', 'TSCL.WINDS_I'), 'EnvPane')

        # Update the window so that the correct geometry is reported
        self.update_idletasks()

        # Set the frame background colour
        self.configure(bg=pbgcolor)

        # For debugging purposes, we needed to report the geometry of the pane
        self.bind("<ButtonRelease-1>", self.geomCB)

        # Establish a link to the audible alert queue
            # clear's below will result in a single clear message each
        self.tempAlert = AudioAlert(
            warnAudio=AU_WARN_LOW_TEMP, warnMinInterval=300)
        self.humAlert = AudioAlert(
            warnAudio=AU_WARN_HIGH_HUMID, warnMinInterval=300,
            alarmAudio=AU_ALARM_HIGH_HUMID, alarmMinInterval=15,
            clearAudio=AU_ALERT_ENV_OK, clearMinInterval=900, clearTimeOut=1200)
        self.windAlert = AudioAlert(
            warnAudio=AU_WARN_HIGH_WIND, warnMinInterval=300,
            alarmAudio=AU_ALARM_HIGH_WIND, alarmMinInterval=15,
            clearAudio=AU_ALERT_ENV_OK, clearMinInterval=900, clearTimeOut=1200)
        self.clear30Alert = AudioAlert(
            clearAudio=AU_ALERT_ENV_OK30, clearMinInterval=1800, clearTimeOut=2100)

        # Create and place the appropriate widgets
        self.TempChart = LineGraph.LineGraph(self, size=(100,300),
                                             gconfig=ENVPANETEMPGRAPH, lconfig=ENVPANETEMPLINES)
        self.TempChart.grid(row=0,column=0)
        
        self.HumChart = LineGraph.LineGraph(self, size=(100,300),
                                            gconfig=ENVPANEHUMGRAPH, lconfig=ENVPANEHUMLINES)
        self.HumChart.grid(row=1,column=0)

        self.WindChart = LineGraph.LineGraph(self, size=(100,300),
                                            gconfig=ENVPANEWSGRAPH, lconfig=ENVPANEWSLINES)
        self.WindChart.grid(row=2,column=0)


    def refresh(self, dict):
        """Update the plot with new values."""
        # We are plotting observation versus time in all charts.
        t = dict['TELSTAT.UNIXTIME'].value()

        # Mute alarm sounds if the dome shutter is closed
        ds = dict['TELSTAT.DOME_CLOSED'].value()
        if ds:
            self.tempAlert.setMute()
            self.humAlert.setMute()
            self.windAlert.setMute()
            self.clear30Alert.setMute()
        else:
            self.tempAlert.clearMute()
            self.humAlert.clearMute()
            self.windAlert.clearMute()
            self.clear30Alert.clearMute()

        # Plot the new temperature values
        Ext = dict['TSCL.TEMP_O'].value()
        Dome =  dict['TSCL.TEMP_I'].value()
        # Validate the incoming data.  Set the background to the alarm colour
        # if invalid data has been received
        if Ext != None and (Ext < -30 or Ext > 30):
            if self.TempChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.TempChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+1, "ERROR (EnvPane:temp chart) Invalid exterior temperature value = %f" % Ext )
            Ext = None
        if Dome != None and (Dome < -30 or Dome > 30):
            if self.TempChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.TempChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+1, "ERROR (EnvPane:temp chart) Invalid dome temperature value = %f" % Dome )
            Dome = None

        if Ext != None and Dome != None:
            # Queue an alert and change the widget to the appropriate background colour
            # if the temperature goes below the warning threshold
            if Ext <= TEMPERATURELOWER:
                if self.TempChart.nowbackground() != PANECOLORYELLOWALERTFOREGROUND:
                    self.TempChart.newbackground(PANECOLORYELLOWALERTFOREGROUND)
                self.tempAlert.alert(level=WARNING)
            elif self.TempChart.nowbackground() != ENVPANEBACKGROUND:
                self.TempChart.newbackground(ENVPANEBACKGROUND)
        self.TempChart.update(t,(Ext,Dome))

        # Plot the new humidity values
        ExtH = dict['TSCL.HUMI_O'].value()
        DomeH =  dict['TSCL.HUMI_I'].value()
        # Since negative or > 100% humidity is impossible, report the bad data
        if ExtH != None and (ExtH < 0 or ExtH > 100):
            if self.HumChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.HumChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+2, "ERROR (EnvPane:humidity chart) Invalid exterior humidity value = %f" % ExtH )
            ExtH = None
        if DomeH != None and (DomeH < 0 or DomeH > 100):
            if self.HumChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.HumChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+2, "ERROR (EnvPane:humidity chart) Invalid dome humidity value = %f" % DomeH )
            DomeH = None
            
        if ExtH != None and DomeH != None:
            # Queue an alert and change the widget to the appropriate background colour
            # if the humidity exceeds the warning or alarm thresholds
            if ExtH >= HUMIDITYUPPER or DomeH >= HUMIDITYUPPER:
                if self.HumChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                    self.HumChart.newbackground(PANECOLORREDALERTFOREGROUND)
                self.humAlert.alert(level=ALARM)
                self.clear30Alert.alert(level=ALARM)
            elif ((ExtH >= HUMIDITYLOWER and ExtH < HUMIDITYUPPER) or (DomeH >= HUMIDITYLOWER and  DomeH < HUMIDITYUPPER)):
                if self.HumChart.nowbackground() != PANECOLORYELLOWALERTFOREGROUND:
                    self.HumChart.newbackground(PANECOLORYELLOWALERTFOREGROUND)
                self.humAlert.alert(level=WARNING)
            elif ExtH < HUMIDITYLOWER and DomeH < HUMIDITYLOWER:
                self.humAlert.alert(level=CLEAR)
                if self.HumChart.nowbackground() != ENVPANEBACKGROUND:
                    self.HumChart.newbackground(ENVPANEBACKGROUND)
        self.HumChart.update(t,(ExtH, DomeH))

        # Plot the new wind speed values
        # Queue an alert and change the widget to the appropriate background colour
        # if the wind speed exceeds the warning or alarm thresholds
        ExtW = dict['TSCL.WINDS_O'].value()
        DomeW =  dict['TSCL.WINDS_I'].value()
        if ExtW != None and ExtW < 0:
            if self.WindChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.WindChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+3, "ERROR (EnvPane:wind chart) Invalid exterior wind speed values = %f" % ExtW )
            ExtW = None
        if DomeW != None and DomeW < 0:
            if self.WindChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                self.WindChart.newbackground(PANECOLORREDALERTFOREGROUND)
            TelStatLog( EnvErrBase+3, "ERROR (EnvPane:wind chart) Invalid wind speed values = %f" % DomeW )
            DomeW = None
            
        if ExtW != None and DomeW != None:
            if ExtW >= WINDSPEEDUPPER or DomeW >= WINDSPEEDUPPER:
                if self.WindChart.nowbackground() != PANECOLORREDALERTFOREGROUND:
                    self.WindChart.newbackground(PANECOLORREDALERTFOREGROUND)
                self.windAlert.alert(level=ALARM)
                self.clear30Alert.alert(level=ALARM)
            elif (ExtW >= WINDSPEEDLOWER and ExtW < WINDSPEEDUPPER) or (DomeW >= WINDSPEEDLOWER and DomeW < WINDSPEEDUPPER):
                if self.WindChart.nowbackground() != PANECOLORYELLOWALERTFOREGROUND:
                    self.WindChart.newbackground(PANECOLORYELLOWALERTFOREGROUND)
                self.windAlert.alert(level=WARNING)
            elif ExtW < WINDSPEEDLOWER and DomeW < WINDSPEEDLOWER:
                self.windAlert.alert(level=CLEAR)
                if self.WindChart.nowbackground() != ENVPANEBACKGROUND:
                    self.WindChart.newbackground(ENVPANEBACKGROUND)
        self.WindChart.update(t,(ExtW, DomeW))

        # Sound the all-clear if humidity and wind speed conditions are met
        if  ExtH < HUMIDITYUPPER and DomeH < HUMIDITYUPPER and \
            ExtW < WINDSPEEDUPPER and DomeW < WINDSPEEDUPPER:
            self.clear30Alert.alert(level=CLEAR)




    def resize(self, paneWidth):
        """Redraw the pane to fit the new width."""
        
        # Update the window so that the correct geometry is reported
        # must be done to assure that geometry != 1x1+0+0
        self.update_idletasks()

        # Compute the new widget dimensions
        graphWidth      = paneWidth
        graphHeight     = int( (self.winfo_height() * 0.86) / 3.0 )
        
        # Update the geometries for the widgets and frame
        self.TempChart.resize( graphHeight, graphWidth )
        self.HumChart.resize(  graphHeight, graphWidth )
        self.WindChart.resize( graphHeight, graphWidth )
        self.configure( height=self.winfo_height(), width=paneWidth )


    def rePack(self):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        self.pack(anchor=NW)
        pass

    
    def tick(self):
        """Update the pane.  For debugging purposes only."""
        self.update()
        self.after(1000, self.tick)


    def geomCB(self, event):
        """Callback for to print geometry."""
        print "Env pane:        ", self.winfo_geometry()

