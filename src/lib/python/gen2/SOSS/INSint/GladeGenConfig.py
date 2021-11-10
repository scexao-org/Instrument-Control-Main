#!/usr/bin/env python

#----------------------------------------------------------------------
# GladeGenConfig.py
# Dave Reed
# 02/03/2004
# Modified by Eric Jeschke  2004.07.29
#----------------------------------------------------------------------

import sys

#----------------------------------------------------------------------

# program author for header of generated file
author = 'Eric Jeschke (eric@naoj.org)'

# date format (this is mm/dd/yyyy)
# see time.strftime format documentation
date_format = '%m/%d/%Y'

# widget types the user wants included in widget list
include_widget_types = [
    'GtkWindow', 'GtkVBox', 'GtkHBox', 'GtkFileChooserDialog',
    'GtkButton', 'GtkSpinButton', 'GtkCheckButton', 'GtkToolbar',
    'GtkToolButton', 'GtkMenuBar', 'GtkScrolledWindow', 'GtkImage',
    'GtkEntry', 'GtkComboBox', 'GtkTextView', 'GtkLabel', 'GtkStatusbar',
    'GtkFrame', 'GtkScrolledWindow', 'GtkDialog'
    ]

#----------------------------------------------------------------------

# default text for class and its methods

class_header = 'class %s(GladeWindow):'

constructor = """
    #----------------------------------------------------------------------

    def __init__(self):

        ''' '''
        
        self.init()

    #----------------------------------------------------------------------

    def init(self):

        ''' '''
        pass

    
"""
        
#----------------------------------------------------------------------

def main(argv):
    pass

#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
