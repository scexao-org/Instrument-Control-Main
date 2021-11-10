#! /usr/local/bin/python

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


    
# validate input value
def validInput(v, Highest, Lowest):

    # user's input to clear entry field
    clearInput = [ 'None', 'none', 'NONE']
    
    # return value after validation
      # nValue[0] is a value to return, default is None
      # if nValue[0] is 0, it indicates that an error occured
      # if nValue[1] is 0,  user input is not the samve as eitehr Highest or Lowest value
      # if nValue[1] is 1,  user input is the samve as either Highest or Lowest value
    nValue = [ 'None', 0 ]
       
    # split current value by '.' if there is one   
    digit = string.split(v, '.')

    # obtain negative sign if there is one
    negV = v[0:1]
                       
    # check if input value is null, 'None', integer, or float
    # in case that input value is null
    if v == '':
        tkMessageBox.showinfo('Validate Input', \
                              'Input Cleared  ')
        return nValue		

    # in case that user input is to clear field
    elif v == clearInput[0] or v == clearInput[1] or v == clearInput[2]:
        return nValue
  
    # in case that input value has decimal point           
    elif '.' in v:
       
        # user input is NNN.nn 
        if len(digit[1]) == 1 or len(digit[1]) == 2:
            pass

        # invalid input    
        else:
            tkMessageBox.showerror('Invalid input', \
                                   'Format: NNN.nn / NNN.n')
            nValue[0] = 0
            return nValue

        # in case of float negative value
        if negV == '-':
            if digit[0][1:].isdigit() and digit[1].isdigit():
                pass
            elif digit[0] == '-' and digit[1].isdigit():
                pass   
            else:
                tkMessageBox.showerror('Invalid input           ', \
                                       'Format: -NNN.nn / -NNN.n')
                nValue[0] = 0
                return nValue

        # in case of float positive value
        else:
            # user input is .NN
            if digit[0] == '' and digit[1].isdigit():
                pass

            # user input is NNN.NN
            elif digit[0].isdigit() and digit[1].isdigit():
               pass

            # invalid input
            else:
                tkMessageBox.showerror('Invalid input', \
                                       'Format: NNN.nn / NNN.n')
                nValue[0] = 0
                return nValue

    # in case that input value does not have decimal point 
    else:

        # user input is negative and digit                         
        if negV == '-' and v[1:].isdigit():
            pass
        
        # user input is digit     
        elif v.isdigit():
            pass

        # invalid input
        else:
            tkMessageBox.showerror('Invalid input', \
                                   'Format: NNN / None')
            nValue[0] = 0
            return nValue
         
    tempV = float(v)

    # if input is -0, take out negative sign
    if tempV == 0.00:
        tempV=0.00
        
    # in case that Highest value is not defined
    if Highest==None:

        # check if user input is equal or greater than Lowest
        if  tempV >= Lowest:
            nValue[0] = '%0.2f' % tempV
            if tempV == Lowest: nValue[1] = 1
        else:
            tkMessageBox.showerror('Invalid Range', \
                                   '%0.2f <= NNN ' % Lowest )
            nValue[0] = 0
            return nValue

    # check if a value is in range (highest - lowest)        
    elif tempV <= Highest and tempV >= Lowest:

        # check user input is equal or less than Highest
        if tempV <= Highest:
         
            # if user input is equal to Highest or Lowest, assign 1
            if tempV == Highest or tempV == Lowest: nValue[1] = 1

        # format return value
        nValue[0] = '%0.2f' % tempV
       
    # user input is out of range   
    else:
               
        tkMessageBox.showerror('Invalid Range', \
                               '%0.2f <= NNN =< %0.2f' %(Lowest, Highest) )

        # assign 0 as an error
        nValue[0] = 0
        return nValue
        

    return nValue		
     

