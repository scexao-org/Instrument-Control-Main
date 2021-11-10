#!/usr/bin/env python


import os
import pango

import pygtk
pygtk.require("2.0")
import gtk
import glib
import gobject
import gtk.glade

gtk.gdk.threads_init()
gobject.threads_init()



class AnaMenuUi(object):

    def __init__(self, logger):
        super(AnaMenuUi, self).__init__()
        self.logger=logger        
        #self.eh=UiEventHandler(logger)

        #self.color="#f5f5f5"
        
       
    def set_ui(self):
        
        color="#E6E6FA"
        
        path=os.path.dirname(__file__)
        gladefile="anamenu.glade"
        
        builder = gtk.Builder()
        
        builder.add_from_file(os.path.join(path,gladefile))

        self.window = builder.get_object("window_ana")
        print self.window

        dic = { #"gtk_main_quit" : self.destory,
               # PROPID
               "toolbutton_propid_toggled_cb": self.set_propid,  

               # VIEWERS
               "toolbutton_fitsviewer_clicked_cb": self.launch_fits_viewer, 
               "toolbutton_telstat_clicked_cb": self.launch_telstat, 
               "toolbutton_skycat_clicked_cb": self.launch_skycat, 
               "toolbutton_ds9_clicked_cb": self.launch_ds9, 
               
               # Instruments
               "toolbutton_spcam_clicked_cb": self.launch_spcam,
               "toolbutton_hds_clicked_cb": self.launch_hds,
               "toolbutton_ircs_clicked_cb": self.launch_ircs,
               "toolbutton_focas_clicked_cb": self.launch_focas,
               "toolbutton_moircs_clicked_cb": self.launch_moircs,
               
               # expander
               "expander_log_activate_cb": self.expand_log,
               # etc
               "toolbutton_quit_clicked_cb": self.quit, 
                }

        builder.connect_signals(dic)

        # close main window 
        if (self.window):
            #self.window.connect("destroy", gtk.main_quit)
            self.window.connect("destroy", self.quit)

        self.logger.debug('building....')

        self.lb_ana_menu = builder.get_object("label_anamenu")
        fontdesc = pango.FontDescription("KouzanBrushFont 16")
        self.lb_ana_menu.modify_font(fontdesc)

        self.entry_propid = builder.get_object("entry_propid")
        self.btn_propid = builder.get_object("toolbutton_propid")
        # propid validation color
        self.attr_list=pango.AttrList()
        self.attr_valid=pango.AttrForeground(0, 45000, 50000, start_index=0, end_index=-1)
        self.attr_invalid=pango.AttrForeground(65535, 0, 0, start_index=0, end_index=-1)


        self.frame_viewers = builder.get_object("frame_viewers")
        #self.frame_viewers.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#111199"))
        #self.frame_viewers.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))
        #f8f8ff  #E6E6FA

        self.frame_ins = builder.get_object("frame_ins")
        #self.frame_ins.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

        self.frame_ins2 = builder.get_object("frame_ins2")
        #self.frame_ins2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

        self.frame_etc = builder.get_object("frame_etc")
        #self.frame_etc.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

            
        self.sw_expander = builder.get_object("sw_expander")
        textview_log = builder.get_object("textview_log")
        self.buffer_log = textview_log.get_buffer()
        #self.frame_status = builder.get_object("frame_status")
        #self.frame_status.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

        #self.statusbar = builder.get_object("statusbar")
        #print self.statusbar

        # datasink button
        self.datasink = builder.get_object("toolbutton_datasink")
        self.datasink.set_sensitive(False)
 
        # anaprog button
        self.anaprog = builder.get_object("toolbutton_anaprog")
        self.anaprog.set_sensitive(False)

      
        self.window.show_all()
        
