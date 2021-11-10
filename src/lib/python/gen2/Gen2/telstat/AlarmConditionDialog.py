#! /usr/local/bin/python

title = ' Alarm Condtion Dialog'

# Import Pmw from this directory tree.
import os
import sys
import Util            
import Pmw
import string
import tkMessageBox

from Tkinter import *
from Tkconstants import *
from TelStat_cfg import *
from StatIO import *
from DispType import *
from AudioPlayer import *
from Alert import *
from validation import *

class  AlarmTest(Frame):

    def __init__(self, parent, pbgcolor=PANECOLORBLUEBACKGROUND	):

        # Create a frame to put the LabeledWidgets into
        Frame.__init__(self, parent)
	
	self.pack(fill = 'both', expand = 1)	
	self.configure(bg=pbgcolor)
	  	
	self._ignoreEvent = 0

        self.scaleHigh = scaleLow = 0.00 

        self.windSpeedLowest = 0.00

        # highest and lowest value of scale and alarm

        # wind speed dome warning high/low
        self.currentWSDWHigh  = self.windSDWHighest = self.windSDWLowest  = self.currentWSDWLow = 0.00

        # wind speed dome alaram high/low
        self.currentWSDAHigh  = self.windSDAHighest = self.windSDALowest  = self.currentWSDALow = 0.00
        
        # wind speed outside warning high/low
        self.currentWSOWHigh  = self.windSOWHighest = self.windSOWLowest  = self.currentWSOWLow = 0.00

        # wind speed outside alaram high/low
        self.currentWSOAHigh  = self.windSOAHighest = self.windSOALowest  = self.currentWSOALow = 0.00

        # temperature dome warning high/low
        self.currentTDWHigh  = self.temperatureDWHighest = self.temperatureDWLowest  = self.currentTDWLow = 0.00

        # temperature outside warning high/low
        self.currentTOWHigh  = self.temperatureOWHighest = self.temperatureOWLowest  = self.currentTOWLow = 0.00

        # humidity dome warning high/low
        self.currentHDWHigh  = self.humidityDWHighest = self.humidityDWLowest  = self.currentHDWLow = 0.00

        # humidity dome alarm high/low
        self.currentHDAHigh  = self.humidityDAHighest = self.humidityDALowest  = self.currentHDALow = 0.00

        # humidity outside warning high/low
        self.currentHOWHigh  = self.humidityOWHighest = self.humidityOWLowest  = self.currentHOWLow = 0.00

        # humidity outside alarm high/low
        self.currentHOAHigh  = self.humidityOAHighest = self.humidityOALowest  = self.currentHOALow = 0.00
        
        self.validation = ''
        
        # default width of entry box       
        defaultWidth=6
 
	# create header
        self.header = self.createFieldLabel(text = 'Low',  font=fontSmallBold, \
                                               bg=pbgcolor, row=0, column=2) 

        self.header = self.createFieldLabel(text = 'High',  font=fontSmallBold, \
                                                bg=pbgcolor, row=0, column=4) 
              
	self.header = Label(self, text = 'Environment', font=fontBold, bg=pbgcolor)
	self.header.grid(column=0, row=1, padx=10,pady=5,  sticky ='w')
   
        self.header = Label(self, text = 'Alarm / Warning', font=fontSmallBold, bg=pbgcolor)
	self.header.grid(columnspan=3, column=1, row=1, sticky ='w')
        
        
	self.header = Label(self, text = 'Warning / Alarm', font=fontSmallBold, bg=pbgcolor)
	self.header.grid(columnspan=5, column=4, row=1, sticky ='w')
    
        # Wind speed dome entry field
        self.windSpeedDomeLabel = self.createFieldLabel(text = 'Wind Speed Dome (m/s)',  font=fontBold, \
                                                        bg=pbgcolor, row=2, column=0) 
        
        # Wind speed dome (alarm:low)
        self.windSDAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=2, column=2)

        # Wind speed dome (warning:low)
        self.windSDWL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=2, column=3)

        # Wind speed dome (warning:high)
        windSDWHigh = self.currentWSDWHigh = WINDSPEEDLOWER
        self.windSDWHighest = WINDSPEEDUPPER
        self.windSDWH = self.createField(value=windSDWHigh,  width=defaultWidth, \
                                         row=2, col=4, valid=self.validate, enter=self.activate )

        # Wind speed dome (alarm:high) 
        windSDAHigh = self.currentWSDAHigh = WINDSPEEDUPPER
        self.windSDAHighest = None
        self.windSDALowest  = 0.00 
        self.currentWSDALow = WINDSPEEDLOWER
        self.windSDAH = self.createField(value=windSDAHigh,  width=defaultWidth, \
                                         row=2, col=5, valid=self.validate, enter=self.activate ) 
     
        # Wind speed outside entry field
        self.windSeedOutSideLabel = self.createFieldLabel(text = 'Wind Speed Outside (m/s)',  font=fontBold, \
                                                          bg=pbgcolor, row=3, column=0) 
      
        # Wind speed outside (alarm:low)
        self.windSOAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=3, column=2)
       
        # Wind speed outside (warning:low)
        self.windSOWL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=3, column=3)
       
        # wind speed outside (warning:high)
        windSOWHigh = self.currentWSOWHigh = WINDSPEEDLOWER
        self.windSOWHighest = WINDSPEEDUPPER
 	self.windSOWH = self.createField(value=windSOWHigh,  width=defaultWidth, \
                                         row=3, col=4, valid=self.validate, enter=self.activate )

        # Wind speed outside (alarm:high) 
        windSOAHigh = self.currentWSOAHigh = WINDSPEEDUPPER
        self.windSOAHighest = None
        self.windSOALowest  = 0.00
        self.currentWSOALow = WINDSPEEDLOWER
        self.windSOAH = self.createField(value=windSOAHigh,  width=defaultWidth, \
                                         row=3, col=5, valid=self.validate, enter=self.activate ) 

        # Temperature dome entry field
        self.temperatureDomeLabel = self.createFieldLabel(text = 'Temperature Dome (C)',  font=fontBold, \
                                                           bg=pbgcolor, row=4, column=0)
        # Temperature dome (alarm:low)
        self.temperatureDAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=4, column=2)

        # Temperature dome (warning:low)
        temperatureDWLow = self.currentTDWLow = TEMPERATURELOWER
        self.temperatureDWHighest = None
        self.temperatureDWLowest = -273.00
        self.temperatureDWL = self.createField(value=temperatureDWLow,  width=defaultWidth, \
                                               row=4, col=3, valid=self.validate, enter=self.activate )

        # Temperature dome (warning:high)
        self.temperatureDWH = self.createNopField( bg=pbgcolor, width=defaultWidth, row=4, column=4)
        
        # Temperature dome (alarm:high)
        self.temperatureDAH = self.createNopField( bg=pbgcolor, width=defaultWidth, row=4, column=5)


        # Temperature outside entry field
        self.temperatureOutSideLabel = self.createFieldLabel(text = 'Temperature Outside (C)',  font=fontBold, \
                                                             bg=pbgcolor, row=5, column=0)
        # Temperature outside (alarm:low)
        self.temperatureOAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=5, column=2)

        # Temperature outside (warning:low)
        temperatureOWLow = self.currentTOWLow = TEMPERATURELOWER
        self.temperatureOWHighest = None
        self.temperatureOWLowest = -273.00
        self.temperatureOWL = self.createField(value=temperatureOWLow,  width=defaultWidth, \
                                               row=5, col=3, valid=self.validate, enter=self.activate )

        # Temperature dome (warning:high)
        self.temperatureOWH = self.createNopField( bg=pbgcolor, width=defaultWidth, row=5, column=4)

        # Temperature dome (alarm:high)
        self.temperatureOAH = self.createNopField( bg=pbgcolor, width=defaultWidth, row=5, column=5)


        # Humidity dome entry field
        self.humidityDomeLabel = self.createFieldLabel(text = 'Humidity Dome (%)',  font=fontBold, \
                                                       bg=pbgcolor, row=6, column=0)

        # Humidity dome (alarm:low)
        self.humidityDAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=6, column=2)

        # Humidity dome (warning:low)
        self.humidityDWL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=6, column=3)
       
        # Humidity dome (warning:high)
        humidityDWHigh = self.currentHDWHigh = HUMIDITYLOWER
        self.humidityDWHighest =  HUMIDITYUPPER
        self.humidityDWLowest = 0.00
        self.humidityDWH = self.createField(value=humidityDWHigh,  width=defaultWidth, \
                                            row=6, col=4, valid=self.validate, enter=self.activate )

        # Humidity dome (alarm:high)
        humidityDAHigh = self.currentHDAHigh = HUMIDITYUPPER
        self.humidityDAHighest = 100.00
        self.humidityDALowest = HUMIDITYLOWER
        self.humidityDAH = self.createField(value=humidityDAHigh,  width=defaultWidth, \
                                            row=6, col=5, valid=self.validate, enter=self.activate )

        # Humidity outside entry field
        self.humidityOutSideLabel = self.createFieldLabel(text = 'Humidity Outside (%)',  font=fontBold, \
                                                          bg=pbgcolor, row=7, column=0)

        # Humidity outside (alarm:low)
        self.humidityOAL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=7, column=2)

        # Humidity outside (warning:low)
        self.humidityOWL = self.createNopField( bg=pbgcolor, width=defaultWidth, row=7, column=3)
                
        # Humidity outside (warning:high)
        humidityOWHigh = self.currentHOWHigh = HUMIDITYLOWER
        self.humidityOWHighest = HUMIDITYUPPER
        self.humidityOWLowest = 0.00
        self.humidityOWH = self.createField(value=humidityOWHigh,  width=defaultWidth, \
                                            row=7, col=4, valid=self.validate, enter=self.activate )

        # Humidity outside (alarm:high)
        humidityOAHigh = self.currentHOAHigh = HUMIDITYUPPER
        self.humidityOAHighest = 100.00
        self.humidityOALowest = HUMIDITYLOWER
        self.humidityOAH = self.createField(value=humidityOAHigh,  width=defaultWidth, \
                                            row=7, col=5, valid=self.validate, enter=self.activate )
        
        # dictionary
	self._wDict = {self.windSDWH:       ("WindSDWHigh"      , validInput) , \
                       self.windSDAH:       ("WindSDAHigh"      , validInput) , \
                       self.windSOWH:       ("WindSOWHigh"      , validInput) , \
                       self.windSOAH:       ("WindSOAHigh"      , validInput) , \
                       self.temperatureDWL: ("TemperatureDWLow" , validInput) , \
                       self.temperatureOWL: ("TemperatureOWLow" , validInput) , \
                       self.humidityDWH:    ("HumidityDWHigh"   , validInput) , \
                       self.humidityDAH:    ("HumidityDAHigh"   , validInput) , \
                       self.humidityOWH:    ("HumidityOWHigh"   , validInput) , \
                       self.humidityOAH:    ("HumidityOAHigh"   , validInput)}

     
    # create field label     
    def createFieldLabel(self, text = '',  font='', bg='',  row=0, column=0): 
        id = Label(self, text = text, font=font, bg=bg)
        id.configure(relief='solid', borderwidth=0)
	id.grid(row=row, column=column, padx=10, pady=5, sticky ='w')
        return id

    # create non option field
    def createNopField(self,  bg='', width=0, row=0, column=0):
        id = Label(self, bg=bg)
        id.configure(width=width, relief='groove', borderwidth=2)
        id.grid(row=row, column=column, padx=5)
        return id
   
    # create entry box 
    def createField(self, value ='',  width=1, row=0, col=0, valid=None, enter=None):
       
      	e= StringVar()
	id = Entry(self, textvariable=e, width=width, takefocus=1, bg=PANECOLORWHITEBACKGROUND)

        # check if a value is None or not, then set up the value
        if value:
             temp = '%0.2f' % value 
	     e.set(temp)
        else:
             e.set(value)

        id.bind('<Shift-Tab>', valid)
        id.bind('<Tab>', valid)
	id.bind('<FocusOut>', valid)
	id.bind('<Return>', valid)
	id.grid(row=row, column=col, padx=5, sticky=W)
	return id

    # testing purpose
    def activate(self, event):
	print '<Return>: value is', event.widget.get()
	print 'call validate in activate'
	self.validate


    # validate wind speed/temperature/humidity warning
    def warning(self, currentValue, Highest, Lowest):
        
        self.valid = self.validator(currentValue, Highest, Lowest)

        # wind dome warning high
        if  self.validation == "WindSDWHigh":

            # get alarm high value
            alarmHigh = self.windSDAH.get()
            
            # check if alarm high has a value or not 
            if alarmHigh == 'None': pass

            else:
                # ignore if usr input is None
                if self.valid[0] == 'None': pass
                # make None if user input is the same as alarm high value
                elif alarmHigh == self.valid[0]: self.valid[0] = 'None'
                # ignore if user input is the same as alarm Lowest value
                elif float(self.valid[0]) == self.windSDWLowest: pass

            # assign user input value as current warnin high value   
            self.currentWSDWHigh = self.valid[0]

        # wind outside warning high
        elif self.validation == "WindSOWHigh":
            alarmHigh = self.windSOAH.get()

            if alarmHigh == 'None': pass

            else:
                if self.valid[0] == 'None': pass
                elif alarmHigh == self.valid[0]: self.valid[0] = 'None'
                elif float(self.valid[0]) == self.windSOWLowest: pass
               
            self.currentWSOWHigh = self.valid[0]

        # temperature dome warning low    
        elif self.validation == "TemperatureDWLow": self.currentTDWLow = self.valid[0]

        # temperature outside warning low
        elif self.validation == "TemperatureOWLow": self.currentTOWLow = self.valid[0]

        # humidity dome warning high
        elif self.validation == "HumidityDWHigh":
            alarmHigh = self.humidityDAH.get()

            if alarmHigh == 'None': pass

            else:
                if self.valid[0] == 'None': pass
                elif alarmHigh == self.valid[0]: self.valid[0] = 'None'
                elif float(self.valid[0]) == self.humidityDAHighest or float(self.valid[0]) == self.humidityDWLowest: pass
                 
            self.currentHDWHigh = self.valid[0]

        # humidity outside warning high 
        elif self.validation == "HumidityOWHigh":
           
            alarmHigh = self.humidityOAH.get()

            if alarmHigh == 'None': pass
                
            else:
                if self.valid[0] == 'None': pass
                elif alarmHigh == self.valid[0]: self.valid[0] = 'None'
                elif float(self.valid[0]) == self.humidityOAHighest or float(self.valid[0]) == self.humidityOWLowest: pass
                             
            self.currentHOWHigh = self.valid[0]

        return None
    
    # validate wind speed/humidity alarm
    def alarm(self, currentValue, Highest, Lowest):
        
        self.valid = self.validator(currentValue, Highest, Lowest)
     
        # in case that user input value is the same as either Highest or Lowest
        if (self.valid[0] and (self.valid[1] == 1)):

            # wind dome alarm high
            if self.validation == "WindSDAHigh":

                # make warning None
                self.windSDWH.delete(0, END)
                self.windSDWH.insert(0, 'None')
                self.currentWSDAHigh = self.valid[0]
                self.currentWSDWHigh = self.windSDWLowest
                
            # wind outside alarm high   
            elif self.validation == "WindSOAHigh":
                self.windSOWH.delete(0, END)
                self.windSOWH.insert(0, 'None')
                self.currentWSOAHigh = self.valid[0]
                self.currentWSOWHigh = self.windSOWLowest
                
            # humidity dome alarm high    
            elif self.validation == "HumidityDAHigh":

                # if alam and warning values are the same, make warning None
                warnHigh = self.humidityDWH.get()
                if warnHigh == self.valid[0]:
                    self.humidityDWH.delete(0, END)
                    self.humidityDWH.insert(0, 'None')
                    self.currentHDWHigh = self.humidityDWLowest

                # assign user input value as current alarm high 
                self.currentHDAHigh = self.valid[0]
                               
            # humidity outsie alarm high   
            elif self.validation == "HumidityOAHigh":
                warnHigh = self.humidityOWH.get()
                if warnHigh == self.valid[0]: 
                    self.humidityOWH.delete(0, END)
                    self.humidityOWH.insert(0, 'None')
                    self.currentHOWHigh = self.humidityOWLowest    

                self.currentHOAHigh = self.valid[0]
                               
            return None
        
        # in case that usr input value is not the same as either Highest or Lowest
        else:
            # wind dome alarm high
            if self.validation == "WindSDAHigh":      self.currentWSDAHigh = self.valid[0]
            
            # wind outside alarm high
            elif self.validation == "WindSOAHigh":    self.currentWSOAHigh = self.valid[0]
            
            # humidity dome alarm high
            elif self.validation == "HumidityDAHigh":
                if self.valid[0] == 'None':           self.currentHDAHigh =  self.humidityDAHighest
                else:                                 self.currentHDAHigh  = self.valid[0]

              
            # humidity outside alarm high    
            elif self.validation == "HumidityOAHigh":
                if self.valid[0] == 'None':           self.currentHOAHigh =  self.humidityOAHighest
                else:                                 self.currentHOAHigh  = self.valid[0]
              
            return None

               
    # choose validation based on an entry field
    def validate(self, event):
	
	while self._ignoreEvent:
	     self._ignoreEvent = 0
	else:
	     currentValue = event.widget.get()
	        
	     self.validation, self.validator = self._wDict[event.widget]
             
             # wind speed, temperature, and humidity  warning high validation 
             if self.validation == "WindSDWHigh"      or self.validation == "WindSOWHigh"      or \
                self.validation == "TemperatureDWLow" or self.validation == "TemperatureOWLow" or \
                self.validation == "HumidityDWHigh"   or self.validation == "HumidityOWHigh":

                # wind dome warning high 
                if self.validation == "WindSDWHigh":

                    # assign Highest and Lowest value
                    Highest = self.currentWSDAHigh
                    Lowest  = float(self.windSDWLowest)

                # wind outside warning high    
                elif self.validation == "WindSOWHigh":
                    Highest = self.currentWSOAHigh
                    Lowest  = float(self.windSOWLowest)

                # temerature dome warning low
                elif self.validation == "TemperatureDWLow":
                    Highest = self.temperatureDWHighest
                    Lowest  = float(self.temperatureDWLowest)

                # temperature outside warning low    
                elif  self.validation == "TemperatureOWLow":
                    Highest = self.temperatureOWHighest
                    Lowest  = float(self.temperatureOWLowest)

                # humidity dome warning high    
                elif self.validation == "HumidityDWHigh":
                    Highest = self.currentHDAHigh
                    Lowest  = float(self.humidityDWLowest)

                # humidity outsie warning high   
                elif self.validation == "HumidityOWHigh":
                    Highest = self.currentHOAHigh
                    Lowest  = float(self.humidityOWLowest)

                # check highest value if it has a value or not
                if Highest == 'None' or Highest == None:
                    Highest = None
                else:
                    Highest  = float(Highest) 
               
                self.warning(currentValue, Highest, Lowest)
              
                 
             # wind speed and humidity alarm high validation  
             elif self.validation == "WindSDAHigh" or  self.validation == "WindSOAHigh" or \
                  self.validation == "HumidityDAHigh" or self.validation ==  "HumidityOAHigh":

                # wind dome alarm high
                if self.validation == "WindSDAHigh":
                    Highest = self.windSDAHighest
                    Lowest  = self.currentWSDWHigh

                # wind outside alarm high    
                elif self.validation == "WindSOAHigh":
                    Highest = self.windSOAHighest
                    Lowest = self.currentWSOWHigh

                # humidity dome alarm high    
                elif self.validation == "HumidityDAHigh":
                    Highest = self.humidityDAHighest
                    Lowest = self.currentHDWHigh

                # humidity outside alarm high  
                elif self.validation == "HumidityOAHigh":
                    Highest = self.humidityOAHighest
                    Lowest = self.currentHOWHigh
                      
                # check lowest value if it has a value or not
                if Lowest == 'None':
                    if   self.validation == "WindSDAHigh":    Lowest = float(self.windSDALowest)
                    elif self.validation == "WindSOAHigh":    Lowest = float(self.windSOALowest)
                    elif self.validation == "HumidityDAHigh": Lowest = float(self.humidityDWLowest)
                    elif self.validation == "HumidityOAHigh": Lowest = float(self.humidityOWLowest)
                else:                                         Lowest = float(Lowest)
                   
                self.alarm(currentValue, Highest, Lowest)

             # update a value in entry field  
	     if self.valid[0]:
                self._ignoreEvent = 1
		event.widget.delete(0, END)
		event.widget.insert(0,self.valid[0])
	     else:
		self._ignoreEvent = 1
		event.widget.focus_set()	

   

############################################################################

# Create Alarm Condition Dialog in root window for testing.
if __name__ == '__main__':
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title(title)

    widget = AlarmTest(root)
    #widget.grid(row=0,column=0)
    #widget.pack()
   
    okButton = Tkinter.Button(root, text = 'OK')
    okButton.pack(side ='left', anchor=SW) 
 
    cancelButton = Tkinter.Button(root, text = 'Cancel', command = root.destroy)
    cancelButton.pack(side = 'right', anchor=SE)
   
   
    root.mainloop()


