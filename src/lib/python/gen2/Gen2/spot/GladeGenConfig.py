#!/usr/bin/env python

#----------------------------------------------------------------------
# GladeGenConfig.py
# Dave Reed
# 02/03/2004
# Modified by Bruce Bon  2005-11-14
#----------------------------------------------------------------------

import sys

#----------------------------------------------------------------------

# program author for header of generated file
author = 'Bruce Bon (Bruce.Bon@SubaruTelescope.org)'

# date format (this is mm/dd/yyyy)
# see time.strftime format documentation
date_format = '%Y-%m-%d'

# widget class names for all widgets that the user wants included in 
# the widget list, for easy access from handlers
include_widget_types = [
    'GtkWindow', 'GtkFileChooserDialog',
    'GtkButton', 'GtkSpinButton', 'GtkCheckButton', 'GtkToolbar',
    'GtkToolButton', 'GtkMenuBar', 'GtkImage',
    'GtkEntry', 'GtkCombo', 'GtkTextView', 'GtkStatusbar',
    'GtkTreeView', 'GtkLabel', 'GtkComboBox', 'GtkComboBoxEntry', 
    'GtkMenuItem', 'GtkImageMenuItem', 'GtkCheckMenuItem',
    'GtkDrawingArea', 'GtkTable',
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
