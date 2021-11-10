#!/usr/bin/env python
#----------------------------------------------------------------------
# Spot.py
# Mark Garboden
# Bruce Bon         2005-11-18 11:32
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Jul 19 17:01:54 HST 2010
#]
#----------------------------------------------------------------------
"""
Usage:
  ./spot.py --loglevel=10 --stderr

"""

import sys
import time
import math

try:
    import gtk
    import gobject
except:
    print "You need to install GTKv2 ",
    print "or set your PYTHONPATH correctly."
    print "try: export PYTHONPATH=",
    print "/usr/lib/python2.X/site-packages/"
    sys.exit(1)

try:
    import p2pgtkGUI
except:
    print "You need to set your PYTHONPATH to include p2pgtkGUI.py",
    print "or you may need to run GladeGen to generate it."
    sys.exit(1)

import plan
import comics
import ssdlog
#import remoteObjects as ro

#----------------------------------------------------------------------


(
    COLUMN_ID,
    COLUMN_NAME
) = range(2)

(
    COLUMN_OFFSET_ID,
    COLUMN_OFFSET_RA,
    COLUMN_OFFSET_DEC,
) = range(3)

# Indices into Activities load list and column indices into Activities ListStore
(   COLUMN_ACTID,
    COLUMN_ACTNAME,
    COLUMN_ACTTAG,
    COLUMN_ACTSTATUS
) = range(4)

# Colors:
TEXTENTRYNORMAL  = gtk.gdk.Color(red=65535, green=65535, blue=65535) # white
TEXTENTRYINVALID = gtk.gdk.Color(red=60000, green=65535, blue=30000) #med yellow
DETECTOR_NOTUSED  = gtk.gdk.Color(red=65535, green=65535, blue=65535) # white
DETECTOR_USED = gtk.gdk.Color(red=60000, green=65535, blue=30000) #med yellow

ID_LABEL = "ID: %s"

UNTITLED_TARGET = "Target_"
UNTITLED_TELCONFIG = "TelConfig_"
UNTITLED_COMICS = "ComicsConfig_"
UNTITLED_DITHER = "DitherConfig_"
UNTITLED_ACTIVITY = "Activity_"

#----------------------------------------------------------------------

class Spot(p2pgtkGUI.p2pgtkGUI):

    def __init__(self, logger, filename=None):
        super(Spot, self).__init__()

        self.logger = logger
        self.logger.debug("Inside Spot constructor")
        self.plan = plan.Plan()
        self.__createEmptyObsPlan()
        self.__createEmptyTargetList()
        self.__createEmptyTelConfigList()
        self.__createEmptyInstConfigList()
        self.__createEmptyDitherList()
        self.__createEmptyOffsetsList()
        self.__setMenuBarAttributes()
        self.__setupComboBoxes()
        self.__setToolBarAttributes()
        #self.widgets['NewTargetButton'].clicked()
        #self.widgets['NewTelButton'].clicked()
        #self.widgets['NewComicsButton'].clicked()
        #self.widgets['NewDitherButton'].clicked()
        #self.widgets['MakeActivity'].clicked()
        self.updateGUI()
        if filename:
          self.filename = filename
          print "Opening",self.filename
          self.plan = plan.ReadPlanFile(self.filename)
          self.updateGUI()
        else:
          self.filename = None
        self.opefilename = None

    def __createEmptyObsPlan(self):
        self.logger.debug("Create an empty observation plan (for now, just activity list).")
        self.ObsPlanListStore = gtk.ListStore(
                gobject.TYPE_UINT, gobject.TYPE_STRING, gobject.TYPE_STRING,
                                                        gobject.TYPE_STRING )

        # column for Activity ID
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_ACTID )
        column.set_sort_column_id( COLUMN_ACTID )
        self.widgets['ObsPlanTreeView'].append_column( column )

        # column for Activity Name
        column = gtk.TreeViewColumn(
                    'Name', gtk.CellRendererText(),text=COLUMN_ACTNAME )
        column.set_sort_column_id( COLUMN_ACTNAME )
        #? column.set_clickable( False )    # turns off sortability
        self.widgets['ObsPlanTreeView'].append_column( column )

        # column for Activity Tag
        column = gtk.TreeViewColumn(
                    'Tag', gtk.CellRendererText(),text=COLUMN_ACTTAG )
        column.set_sort_column_id( COLUMN_ACTTAG )
        self.widgets['ObsPlanTreeView'].append_column( column )

        # column for Activity Status
        column = gtk.TreeViewColumn(
                    'Status', gtk.CellRendererText(),text=COLUMN_ACTSTATUS )
        column.set_sort_column_id( COLUMN_ACTSTATUS )
        self.widgets['ObsPlanTreeView'].append_column( column )

    def __createEmptyTargetList(self):
        self.logger.debug("Create an empty target list.")
        # Initialize targets ListStore (the model) and find the targets TreeView
        self.targetsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        # column for Target Name
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_ID )
        column.set_sort_column_id( COLUMN_ID )
        self.widgets['TargetsTreeView'].append_column( column )

        # column for Target Name
        column = gtk.TreeViewColumn(
                    'Target', gtk.CellRendererText(),text=COLUMN_NAME )
        column.set_sort_column_id( COLUMN_NAME )
        self.widgets['TargetsTreeView'].append_column( column )
        # adjustments didn't work
        #hadjustment = self.widgets['TargetsTreeView'].get_hadjustment()
        #adjustment = gtk.Adjustment()
        #self.widgets['TargetsTreeView'].set_hadjustment(hadjustment)
        #print adjustment,hadjustment

    def __createEmptyTelConfigList(self):
        self.logger.debug("Create an empty telConfig list.")
        # Initialize telConfig ListStore (the model) and find the telConfig TreeView
        self.telConfigsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        # column for telConfig Name
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_ID )
        column.set_sort_column_id( COLUMN_ID )
        self.widgets['TelTreeView'].append_column( column )

        # column for Target Name
        column = gtk.TreeViewColumn(
                    'Name', gtk.CellRendererText(),text=COLUMN_NAME )
        column.set_sort_column_id( COLUMN_NAME )
        self.widgets['TelTreeView'].append_column( column )

    def __createEmptyInstConfigList(self):
        self.logger.debug("Create an empty instConfig list.")
        # Initialize instConfig ListStore (the model) and find the instConfig TreeView
        self.instConfigsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        # column for instConfig Name
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_ID )
        column.set_sort_column_id( COLUMN_ID )
        self.widgets['ComicsTreeView'].append_column( column )

        # column for InstConfig Name
        column = gtk.TreeViewColumn(
                    'Name', gtk.CellRendererText(),text=COLUMN_NAME )
        column.set_sort_column_id( COLUMN_NAME )
        self.widgets['ComicsTreeView'].append_column( column )

    def __createEmptyDitherList(self):
        self.logger.debug("Create an empty dither list.")
        # Initialize dithers ListStore (the model) and find the Dithers TreeView
        self.dithersListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        # column for Target Name
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_ID )
        column.set_sort_column_id( COLUMN_ID )
        self.widgets['DithersTreeView'].append_column( column )

        # column for Dither Name
        column = gtk.TreeViewColumn(
                    'Dither', gtk.CellRendererText(),text=COLUMN_NAME )
        column.set_sort_column_id( COLUMN_NAME )
        self.widgets['DithersTreeView'].append_column( column )

    def __createEmptyOffsetsList(self):
        self.logger.debug("Create an empty offsets list.")
        # Initialize offsets ListStore (the model) and find the Offsets TreeView
        self.offsetsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                            gobject.TYPE_STRING,gobject.TYPE_STRING )

        # column for Offset ID
        column = gtk.TreeViewColumn(
                    'ID', gtk.CellRendererText(),text=COLUMN_OFFSET_ID )
        column.set_sort_column_id( COLUMN_OFFSET_ID )
        self.widgets['OffsetsTreeView'].append_column( column )

        cellrenderertextRA = gtk.CellRendererText()
        cellrenderertextRA.set_property('editable', True)
        cellrenderertextRA.connect('edited', self.cb_DitherOffset_edited,
                                                         COLUMN_OFFSET_RA)
        # column for Offset RA
        column = gtk.TreeViewColumn(
                    'RA', cellrenderertextRA,text=COLUMN_OFFSET_RA )
        column.set_sort_column_id( COLUMN_OFFSET_RA )
        self.widgets['OffsetsTreeView'].append_column( column )

        cellrenderertextDec = gtk.CellRendererText()
        cellrenderertextDec.set_property('editable', True)
        cellrenderertextDec.connect('edited', self.cb_DitherOffset_edited,
                                                         COLUMN_OFFSET_DEC)
        # column for Offset Dec
        column = gtk.TreeViewColumn(
                    'Dec', cellrenderertextDec,text=COLUMN_OFFSET_DEC )
        column.set_sort_column_id( COLUMN_OFFSET_DEC )
        self.widgets['OffsetsTreeView'].append_column( column )

    def __setMenuBarAttributes(self):
        self.logger.debug("Set MenuBar attributes.")
        # Set file menu sensitivity flags
        #? self.widgets['save_obsplan'].set_sensitive( False )
        ##self.widgets['make_opefile'].set_sensitive( False )
        # Set Edit menu VISIBLE flags off for future capabilities
        self.widgets['undo'].unset_flags( gtk.VISIBLE )
        self.widgets['redo'].unset_flags( gtk.VISIBLE )
        self.widgets['cut_activity'].unset_flags( gtk.VISIBLE )
        self.widgets['copy_activity'].unset_flags( gtk.VISIBLE )
        self.widgets['paste_activity'].unset_flags( gtk.VISIBLE )
        self.widgets['delete_activity'].unset_flags( gtk.VISIBLE )
        # Set View and Connection menus VISIBLE flags off
        self.widgets['ViewMenu'].unset_flags( gtk.VISIBLE )
        #self.widgets['ConnectionMenu'].unset_flags( gtk.VISIBLE )
        self.widgets['disconnect_from_server'].unset_flags( gtk.VISIBLE )

    def __setToolBarAttributes(self):
        self.logger.debug("Set ToolBar attributes.")
        # Set AddNote and AddGroup VISIBLE flags off
        self.widgets['AddNote'].unset_flags( gtk.VISIBLE )
        self.widgets['AddGroup'].unset_flags( gtk.VISIBLE )
        # Set ImportActivity sensitivity flag False
        self.widgets['ClearActivity'].unset_flags( gtk.VISIBLE )
        self.widgets['ImportActivity'].unset_flags( gtk.VISIBLE )
        self.widgets['ImportActivity'].set_sensitive( False )
        # Set UT selector and display VISIBLE flags off
        self.widgets['UTselection'].unset_flags( gtk.VISIBLE )
        self.widgets['UTlabel'].unset_flags( gtk.VISIBLE )

    def __setupComboBoxes(self):
        self.logger.debug("set up combo boxes.")
        # activity status
        combobox = self.widgets['ActivityStatusSelection']
        for i,string in enumerate(comics.Activity.STATUS_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(comics.Activity.STATUS[comics.Activity.DEF_STATUS])

        # target equinox
        combobox = self.widgets['TargetEquinoxSelection']
        for i,string in enumerate(plan.Target.TARGET_EQUINOX_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(plan.Target.TARGET_EQUINOX[plan.Target.DEF_EQUINOX])

        # target equinox
        combobox = self.widgets['TargetStyleSelection']
        for i,string in enumerate(plan.Target.TARGET_STYLE_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(plan.Target.TARGET_STYLE[plan.Target.DEF_STYLE])

        # comics readout priority
        combobox = self.widgets['ReadoutPrioritySelection']
        for i,string in enumerate(comics.InstConfig.READOUT_PRIORITY_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(comics.InstConfig.READOUT_PRIORITY[
                                      comics.InstConfig.DEF_READOUT_PRIORITY])

        # comics Slit Width
        combobox = self.widgets['SlitWidthSelection']
        for i,string in enumerate(comics.InstConfig.SLIT_WIDTH_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(comics.InstConfig.SLIT_WIDTH[
                                      comics.InstConfig.DEF_SLIT_WIDTH])

        # comics Comics Mode
        combobox = self.widgets['ComicsModeSelection']
        for i,string in enumerate(comics.COMICS_MODE_STRS):
          combobox.insert_text(i,string)
        combobox.set_active(comics.COMICS_MODE[
                                      comics.InstConfig.DEF_COMICS_MODE])

        # comics Imaging filter
        combobox = self.widgets['ImagingFilterSelection']
        for i,string in enumerate(comics.COMBO[comics.InstConfig.DEF_COMICS_MODE]):
          combobox.insert_text(i,string)
        combobox.set_active(0)


#----------------------------------------------------------------------

    def cb_TargetNameEntryFocusOut(self, *args):
        self.logger.debug("cb_TargetNameEntryFocusOut called")
        selected = self.widgets['TargetsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        (i,) = model.get(itr, 0, )
        #print i
        new_name = self.widgets['TargetNameEntry'].get_text()
        self.plan.targets[int(i)].name = new_name
        model.set(itr, 1, new_name)
        #? don't think we need this any more: we use EntryChanged
        

    def cb_DithNameEntryFocusOut(self, *args):
        self.logger.debug("cb_DithNameEntryFocusOut called")
        selected = self.widgets['DithersTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        (i,) = model.get(itr, 0, )
        #print i
        new_name = self.widgets['DithNameEntry'].get_text()
        self.plan.dithers[int(i)].name = new_name
        model.set(itr, 1, new_name)
        #? don't think we need this any more: we use EntryChanged



##  New  #######################################

    def cb_NewTarget( self, *args ):
        self.logger.debug("cb_NewTarget was called!!!!!")
        new_target = plan.Target()
        index = len(self.plan.targets)
        new_target.name = UNTITLED_TARGET+str(index)
        self.plan.targets.append(new_target)
        itr = self.targetsListStore.append()
        self.targetsListStore.set( itr,
                COLUMN_ID, index,
                COLUMN_NAME, new_target.name )
        self.widgets['TargetsTreeView'].set_model(self.targetsListStore)
        selection = self.widgets['TargetsTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateTargetSpec()

    def cb_NewTelRecipe( self, *args ):
        self.logger.debug("cb_NewTelRecipe was called!!!!!")
        new_telConfig = comics.TelConfig()
        index = len(self.plan.telConfigs)
        new_telConfig.name = UNTITLED_TELCONFIG+str(index)
        self.plan.telConfigs.append(new_telConfig)
        itr = self.telConfigsListStore.append()
        self.telConfigsListStore.set( itr,
                COLUMN_ID, index,
                COLUMN_NAME, new_telConfig.name )
        self.widgets['TelTreeView'].set_model(self.telConfigsListStore)
        selection = self.widgets['TelTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateTelConfigSpec()

    def cb_NewComicsRecipe( self, *args ):
        self.logger.debug("cb_NewComicsRecipe was called!!!!!")
        new_instConfig = comics.InstConfig()
        index = len(self.plan.instConfigs)
        new_instConfig.name = UNTITLED_COMICS+str(index)
        self.plan.instConfigs.append(new_instConfig)
        itr = self.instConfigsListStore.append()
        self.instConfigsListStore.set( itr,
                COLUMN_ID, index,
                COLUMN_NAME, new_instConfig.name )
        self.widgets['ComicsTreeView'].set_model(self.instConfigsListStore)
        selection = self.widgets['ComicsTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateInstConfigSpec()

    def cb_NewDithRecipe( self, *args ):
        self.logger.debug("cb_NewDitherRecipe was called!!!!!")
        new_dither = comics.Dither()
        index = len(self.plan.dithers)
        new_dither.name = UNTITLED_DITHER+str(index)
        self.plan.dithers.append(new_dither)
        itr = self.dithersListStore.append()
        self.dithersListStore.set( itr,
                COLUMN_ID, index,
                COLUMN_NAME, new_dither.name )
        self.widgets['DithersTreeView'].set_model(self.dithersListStore)
        selection = self.widgets['DithersTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateDitherSpec()


    def on_AddActivity_clicked(self, *args):
        self.logger.debug("on_AddActivity_clicked called")
        # Find iterators, etc.
        (target_i,model,itr) = self.FindTreeSelection('TargetsTreeView')
        (telConfig_i,model,itr) = self.FindTreeSelection('TelTreeView')
        (instConfig_i,model,itr) = self.FindTreeSelection('ComicsTreeView')
        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i

        # Validate iterators -- have all components been selected?
        ok = True
        if  target_i == None:
            self.logger.warning( "Make Activity: Can't create new activity because no Target selected" )
            ok = False
        if  telConfig_i == None:
            self.logger.warning( "Make Activity: Can't create new activity because no Telescope Recipe selected" )
            ok = False
        if  instConfig_i == None:
            self.logger.warning( "Make Activity: Can't create new activity because no COMICS Recipe selected" )
            ok = False
        if  dither_i == None:
            self.logger.warning( "Make Activity: Can't create new activity because no Dither Recipe selected" )
            ok = False
        #?? Should pop-up a warning here.
        if  not ok:
            return

        # Validate components -- if fails, don't create activity
        valid = self.plan.targets[int(target_i)].isValid()
        if  valid != True:
            self.logger.warning( "Make Activity: Can't create new activity because target is invalid" )
            #?? Should pop-up a warning here.
            return
        #?? Similar tests for Tel, Comics, Dithers

        # Create new activity and add it to the list and all widgets
        index = len(self.plan.activities)
        new_activity = comics.Activity(self.plan.targets[int(target_i)],
                                       self.plan.telConfigs[int(telConfig_i)],
                                       self.plan.instConfigs[int(instConfig_i)],
                                       self.plan.dithers[int(dither_i)])
        new_activity.name = UNTITLED_ACTIVITY+str(index)
        self.plan.activities.append(new_activity)

        itr = self.ObsPlanListStore.append()
        self.ObsPlanListStore.set( itr,
                COLUMN_ID, index,
                COLUMN_ACTNAME, new_activity.name,
                COLUMN_ACTTAG, new_activity.tag,
                COLUMN_ACTSTATUS, new_activity.status )
        self.widgets['ObsPlanTreeView'].set_model(self.ObsPlanListStore)
        selection = self.widgets['ObsPlanTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.updateActivitySpec()

    def on_SetDefCentralWavelengthButton_clicked(self, *args):
        self.logger.debug("on_SetDefCentralWavelengthButton_clicked called")
        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          self.widgets['CentralWavelengthEntry'].set_text('')
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          self.widgets['CentralWavelengthEntry'].set_text(
               comics.CENTRAL_WAVELENGTH[self.plan.instConfigs[int(i)].mode])


    def on_AddOriginButton_clicked(self, *args):
        self.logger.debug("on_AddOffsetButton_clicked called")
        self.AddOffset('0.0','0.0')

    
    def on_AddOffsetButton_clicked(self, *args):
        self.logger.debug("on_AddOriginButton_clicked called")
        self.AddOffset('+1.0','+1.0')

    def AddOffset(self, ra,dec):
        self.logger.debug("on_AddOriginButton_clicked called")

        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i

        index = len(self.plan.dithers[int(dither_i)].offsets)
        self.plan.dithers[int(dither_i)].offsets.append([ra,dec])

        itr = self.offsetsListStore.append()
        self.offsetsListStore.set( itr,
                COLUMN_OFFSET_ID, index,
                COLUMN_OFFSET_RA, self.plan.dithers[int(dither_i)].offsets[index][0],
                COLUMN_OFFSET_DEC, self.plan.dithers[int(dither_i)].offsets[index][1])
        self.widgets['OffsetsTreeView'].set_model(self.offsetsListStore)
        selection = self.widgets['OffsetsTreeView'].get_selection()
        #print "selection",selection
        selection.select_iter(itr)
        self.updateDitherSpec()


    def on_MoveOffsetDownButton_clicked(self, *args):
        self.logger.debug("on_MoveOffsetDownButton_clicked called")

        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i
        (offset_i,model,itr) = self.FindTreeSelection('OffsetsTreeView')
        offset_i = int(offset_i)
        new_offset_i = min(offset_i+1,len(self.plan.dithers[int(dither_i)].offsets)-1)
        saved = self.plan.dithers[int(dither_i)].offsets.pop(offset_i)
        self.plan.dithers[int(dither_i)].offsets.insert(new_offset_i ,saved)

        itr = self.offsetsListStore.clear()
        for index in range(len(self.plan.dithers[int(dither_i)].offsets)):
          itr = self.offsetsListStore.append()
          self.offsetsListStore.set( itr,
                COLUMN_OFFSET_ID, index,
                COLUMN_OFFSET_RA, self.plan.dithers[int(dither_i)].offsets[index][0],
                COLUMN_OFFSET_DEC, self.plan.dithers[int(dither_i)].offsets[index][1])
        #
        #self.widgets['OffsetsTreeView'].set_model(self.offsetsListStore)
        selection = self.widgets['OffsetsTreeView'].get_selection()
        selection.select_path(new_offset_i)
        self.updateDitherSpec()


    def on_MoveOffsetUpButton_clicked(self, *args):
        self.logger.debug("on_MoveOffsetDownButton_clicked called")

        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i
        (offset_i,model,itr) = self.FindTreeSelection('OffsetsTreeView')
        offset_i = int(offset_i)
        new_offset_i = max(0,offset_i-1) 
        saved = self.plan.dithers[int(dither_i)].offsets.pop(offset_i)
        self.plan.dithers[int(dither_i)].offsets.insert(new_offset_i,saved)

        itr = self.offsetsListStore.clear()
        for index in range(len(self.plan.dithers[int(dither_i)].offsets)):
          itr = self.offsetsListStore.append()
          self.offsetsListStore.set( itr,
                COLUMN_OFFSET_ID, index,
                COLUMN_OFFSET_RA, self.plan.dithers[int(dither_i)].offsets[index][0],
                COLUMN_OFFSET_DEC, self.plan.dithers[int(dither_i)].offsets[index][1])
        #
        #self.widgets['OffsetsTreeView'].set_model(self.offsetsListStore)
        selection = self.widgets['OffsetsTreeView'].get_selection()
        selection.select_path((new_offset_i,))
        self.updateDitherSpec()


    def on_DeleteOffsetButton_clicked(self, *args):
        self.logger.debug("on_DeleteOffsetButton_clicked called")

        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i
        (offset_i,model,itr) = self.FindTreeSelection('OffsetsTreeView')
        offset_i = int(offset_i)
        self.plan.dithers[int(dither_i)].offsets.pop(offset_i)
        result = self.offsetsListStore.remove(itr)

        #need to refill the listStore so the IDs are contiguous
        itr = self.offsetsListStore.clear()
        for index in range(len(self.plan.dithers[int(dither_i)].offsets)):
          itr = self.offsetsListStore.append()
          self.offsetsListStore.set( itr,
                COLUMN_OFFSET_ID, index,
                COLUMN_OFFSET_RA, self.plan.dithers[int(dither_i)].offsets[index][0],
                COLUMN_OFFSET_DEC, self.plan.dithers[int(dither_i)].offsets[index][1])
        #
        #self.widgets['OffsetsTreeView'].set_model(self.offsetsListStore)
        selection = self.widgets['OffsetsTreeView'].get_selection()
        selection.select_path((offset_i,))
        self.updateDitherSpec()


    def cb_DitherOffset_edited(self,cell, path, new_text, col_num):
        self.logger.debug("cb_DitherOffset_edited %s %s %s %s" % (cell,path,new_text,col_num))
        if COLUMN_OFFSET_RA == col_num:
          ra_or_dec = 0
        else:
          ra_or_dec = 1
        self.offsetsListStore[path][col_num] = new_text
        (dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        #print dither_i
        self.plan.dithers[int(dither_i)].offsets[int(path)][ra_or_dec] = new_text
        #?reflect this back into the model!?
        #return


        

    def on_oAcctEntry_changed(self, *args):
        self.logger.debug("on_oAcctEntry_changed")
        self.plan.oAcct = self.widgets['oAcctEntry'].get_text()



## Spec name changed ########################

    def FindTreeSelection(self,treeView):
        self.logger.debug("FindTreeSelection %s" % treeView)
        selected = self.widgets[treeView].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:  # there was no selection
          i = None
        else:  # get the selection index
          (i,) = model.get(itr, 0, )
        #print i
        return(i, model, itr)

    def EntryChangeIntoTree(self, entry, column, treeView):
        self.logger.debug("EntryChangeIntoTree %s %s %s" % (entry, column, treeView))
        (i, model, itr) = self.FindTreeSelection(treeView)
        if itr == None:
          new_name = ""
        else:  # there is a selection
          new_name = self.widgets[entry].get_text()
          model.set(itr, column, new_name)
        return(i,new_name)

    def EntryChange(self, entry, treeView):
        self.logger.debug( "EntryChange")
        (i, model, itr) = self.FindTreeSelection(treeView)
        new_name = self.widgets[entry].get_text()
        return(i,new_name)

    def CheckToggled(self, entry, treeView):
        self.logger.debug( "CheckToggled")
        (i, model, itr) = self.FindTreeSelection(treeView)
        new_val = self.widgets[entry].get_active()
        return(i,new_val)

    def SpinChanged(self, entry, treeView):
        self.logger.debug( "SpinChanged")
        (i, model, itr) = self.FindTreeSelection(treeView)
        new_val = self.widgets[entry].get_value_as_int()
        return(i,new_val)


    def on_TargetNameEntry_changed(self, *args):
        self.logger.debug("on_TargetNameEntry_changed")
        (i,new_name) = self.EntryChangeIntoTree('TargetNameEntry',
                                                COLUMN_NAME,'TargetsTreeView')
        self.plan.targets[int(i)].name = new_name
        self.updateTargetSpec()

    def on_TargetRAEntry_changed(self, *args):
        self.logger.debug("on_TargetRAEntry_changed")
        (i,new_ra) = self.EntryChange('TargetRAEntry','TargetsTreeView')
        self.plan.targets[int(i)].ra = new_ra
        self.updateTargetSpec()
        val = self.plan.targets[int(i)].isValid( ('ra',) )
        # NOTE: MUST test "== True" because non-None/non-False counts as True!
        if  val == True:
            # RA is valid -- set background to normal
            self.widgets['TargetRAEntry'].modify_base( 
                                        gtk.STATE_NORMAL, TEXTENTRYNORMAL )
            return
        # RA is invalid -- set background to yellow
        self.logger.debug( 'Target.RA turning to yellow: %s' % val['ra'] )
        self.widgets['TargetRAEntry'].modify_base( 
                                        gtk.STATE_NORMAL, TEXTENTRYINVALID )

    def on_TargetDecEntry_changed(self, *args):
        self.logger.debug("on_TargetDecEntry_changed")
        (i,new_value) = self.EntryChange('TargetDecEntry','TargetsTreeView')
        self.plan.targets[int(i)].dec = new_value
        self.updateTargetSpec()
        val = self.plan.targets[int(i)].isValid( ('dec',) )
        # NOTE: MUST test "== True" because non-None/non-False counts as True!
        if  val == True:
            # DEC is valid -- set background to normal
            self.widgets['TargetDecEntry'].modify_base( 
                                        gtk.STATE_NORMAL, TEXTENTRYNORMAL )
            return
        # DEC is invalid -- set background to yellow
        self.logger.debug( 'Target.DEC turning to yellow: %s' % val['dec'] )
        self.widgets['TargetDecEntry'].modify_base( 
                                        gtk.STATE_NORMAL, TEXTENTRYINVALID )


    def on_TelNameEntry_changed(self, *args):
        #print "on_TelNameEntry_changed"
        (i,new_name) = self.EntryChangeIntoTree('TelNameEntry',
                                                COLUMN_NAME,'TelTreeView')
        self.plan.telConfigs[int(i)].name = new_name
        self.updateTelConfigSpec()

    def on_ChopThrowEntry_changed(self, *args):
        self.logger.debug("on_ChopThrowEntry_changed")
        (i,new_value) = self.EntryChange('ChopThrowEntry','TelTreeView')
        self.plan.telConfigs[int(i)].chop.throw = new_value
        self.updateTelConfigSpec()

    def on_DefChopPAcheck_toggled(self, *args):
        (i,new_value) = self.CheckToggled('DefChopPAcheck','TelTreeView')
        self.plan.telConfigs[int(i)].chop.use_def_pa = new_value
        self.updateTelConfigSpec()
        
    def on_UseNoddingcheck_toggled(self, *args):
        (i,new_value) = self.CheckToggled('UseNoddingcheck','TelTreeView')
        self.plan.telConfigs[int(i)].use_nodding = new_value
        self.updateTelConfigSpec()
        
    def on_DefNodPAcheck_toggled(self, *args):
        (i,new_value) = self.CheckToggled('DefNodPAcheck','TelTreeView')
        self.plan.telConfigs[int(i)].nod.use_def_pa = new_value
        self.updateTelConfigSpec()
        

    def on_ChopPAEntry_changed(self, *args):
        self.logger.debug("on_ChopPAEntry_changed")
        (i,new_value) = self.EntryChange('ChopPAEntry','TelTreeView')
        self.plan.telConfigs[int(i)].chop.pa = new_value
        self.updateTelConfigSpec()

    def on_NodThrowEntry_changed(self, *args):
        self.logger.debug("on_NodThrowEntry_changed")
        (i,new_value) = self.EntryChange('NodThrowEntry','TelTreeView')
        self.plan.telConfigs[int(i)].nod.throw = new_value
        self.updateTelConfigSpec()

    def on_NodPAEntry_changed(self, *args):
        self.logger.debug("on_nodPAEntry_changed")
        (i,new_value) = self.EntryChange('NodPAEntry','TelTreeView')
        self.plan.telConfigs[int(i)].nod.pa = new_value
        self.updateTelConfigSpec()

    def on_TelInstPAEntry_changed(self, *args):
        #print "on_TelInstPAEntry_changed"
        (i,new_value) = self.EntryChange('TelInstPAEntry','TelTreeView')
        self.plan.telConfigs[int(i)].inst_pa = new_value
        self.updateTelConfigSpec()

    def on_TelXOffsetEntry_changed(self, *args):
        #print "on_TelXOffsetEntry_changed"
        (i,new_value) = self.EntryChange('TelXOffsetEntry','TelTreeView')
        self.plan.telConfigs[int(i)].offset[0] = new_value
        self.updateTelConfigSpec()

    def on_TelYOffsetEntry_changed(self, *args):
        #print "on_TelYOffsetEntry_changed"
        (i,new_value) = self.EntryChange('TelYOffsetEntry','TelTreeView')
        self.plan.telConfigs[int(i)].offset[1] = new_value
        self.updateTelConfigSpec()

    def on_UseGuidingcheck_toggled(self, *args):
        (i,new_value) = self.CheckToggled('UseGuidingcheck','TelTreeView')
        if None != i:
          self.plan.telConfigs[int(i)].use_autoguide = new_value
        self.updateTelConfigSpec()
        


    def on_IntegTimeEntry_changed(self, *args):
        self.logger.debug("on_IntegTimeEntry_changed")
        (i,new_value) = self.EntryChange('IntegTimeEntry','ComicsTreeView')
        self.plan.instConfigs[int(i)].integ_time_per_beam = new_value
        self.updateInstConfigSpec()

    def on_CentralWavelengthEntry_changed(self, *args):
        self.logger.debug("on_CentralWavelengthEntry_changed")
        (i,new_value) = self.EntryChange('CentralWavelengthEntry','ComicsTreeView')
        self.plan.instConfigs[int(i)].center_wavelength = new_value
        self.updateInstConfigSpec()



    def on_ComicsNameEntry_changed(self, *args):
        self.logger.debug("on_ComicsNameEntry_changed")
        (i,new_name) = self.EntryChangeIntoTree('ComicsNameEntry',
                                                COLUMN_NAME,'ComicsTreeView')
        self.plan.instConfigs[int(i)].name = new_name
        self.updateInstConfigSpec()



    def on_DithNameEntry_changed(self, *args):
        self.logger.debug("on_DithNameEntry_changed")
        (i,new_name) = self.EntryChangeIntoTree('DithNameEntry',
                                                COLUMN_NAME,'DithersTreeView')
        self.plan.dithers[int(i)].name = new_name
        self.updateDitherSpec()

    def on_PosAdjustcheck_toggled(self, *args):
        self.logger.debug("on_PosAdjustcheck_toggled called")
        (i,new_value) = self.CheckToggled('PosAdjustcheck','DithersTreeView')
        self.plan.dithers[int(i)].pos_adjust = new_value
        self.updateDitherSpec()
        
    def on_RepeatSpin_changed(self, *args):
        self.logger.debug("on_RepeatSpin_toggled called")
        (i,new_value) = self.SpinChanged('RepeatSpin','DithersTreeView')
        self.plan.dithers[int(i)].repeat = new_value
        self.updateDitherSpec()
        return(False)

    def on_UseDitheringCheck_toggled(self, *args):
        self.logger.debug("on_UseDitheringCheck_toggled called")
        (i,new_value) = self.CheckToggled('UseDitheringCheck','DithersTreeView')
        self.plan.dithers[int(i)].use_dithering = new_value
        self.updateDitherSpec()
        


    def on_ActivityNameEntry_changed(self, *args):
        self.logger.debug("on_ActivityNameEntry_changed")
        (i,new_name) = self.EntryChangeIntoTree('ActivityNameEntry',
                                                COLUMN_ACTNAME,'ObsPlanTreeView')
        if i != None:  # i.e. there was a selection
          self.plan.activities[int(i)].name = new_name
          self.updateActivitySpec()  #? inside or outside the if??

    def on_ActivityCommentEntry_changed(self, *args):
        self.logger.debug("on_ActivityCommentEntry_changed")
        (i,new_name) = self.EntryChange('ActivityCommentEntry','ObsPlanTreeView')
        if i != None:
          self.plan.activities[int(i)].comment = new_name
          self.updateActivitySpec()

    def on_ActivityTagEntry_changed(self, *args):
        self.logger.debug("on_ActivityTagEntry_changed")
        (i,new_name) = self.EntryChangeIntoTree('ActivityTagEntry',
                                             COLUMN_ACTTAG,'ObsPlanTreeView')
        if i != None:
          self.plan.activities[int(i)].tag = new_name
          self.updateActivitySpec()


## TreeView cursor changed  ###########

    def UnselectObsPlanTreeView(self):
        (obsplan_i,model,itr) = self.FindTreeSelection('ObsPlanTreeView')
        if itr != None:  # there is a selection to deselect
          selection = self.widgets['ObsPlanTreeView'].get_selection()
          selection.unselect_iter(itr)
          self.updateActivitySpec()  
        #


    def on_TargetsTreeView_cursor_changed(self, *args):
        self.logger.debug("on_TargetsTreeView_cursor_changed was called!!")
        #selected = args[0].get_selection()
        #(model,itr)  = selected.get_selected()
        #(id, name) = model.get(itr, 0, 1)
        #print id,name
        ## Don't think you need all the above junk any more
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateTargetSpec()
        
    def on_TelTreeView_cursor_changed(self, *args):
        self.logger.debug("on_TelTreeView_cursor_changed was called!!")
        #selected = args[0].get_selection()
        #(model,itr)  = selected.get_selected()
        #(id, name) = model.get(itr, 0, 1)
        #print id,name
        ## Don't think you need all the above junk any more
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateTelConfigSpec()

    def on_ComicsTreeView_cursor_changed(self, *args):
        self.logger.debug("on_ComicsTreeView_cursor_changed was called!!")
        #selected = args[0].get_selection()
        #(model,itr)  = selected.get_selected()
        #(id, name) = model.get(itr, 0, 1)
        #print id,name
        ## Don't think you need all the above junk any more
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateInstConfigSpec()

    def on_DithersTreeView_cursor_changed(self, *args):
        self.logger.debug("on_DithersTreeView_cursor_changed was called!!")
        #selected = args[0].get_selection()
        #(model,itr)  = selected.get_selected()
        #(id, name) = model.get(itr, 0, 1)
        #print id,name
        ## Don't think you need all the above junk any more
        self.UnselectObsPlanTreeView()
        self.updateToolArea()
        self.updateDitherSpec()

    def on_OffsetsTreeView_cursor_changed(self, *args):
        self.updateDitherSpec()


    def on_ObsPlanTreeView_cursor_changed(self, *args):
        self.logger.debug("on_ObsPlanTreeView_cursor_changed was called!!")
        #selected = args[0].get_selection()
        #(model,itr)  = selected.get_selected()
        #(id, name) = model.get(itr, 0, 1)
        #print id,name
        ## Don't think you need all the above junk any more

        #(target_i,model,target_itr) = self.FindTreeSelection('TargetsTreeView')
        #(telConfig_i,model,itr) = self.FindTreeSelection('TelTreeView')
        #(instConfig_i,model,itr) = self.FindTreeSelection('ComicsTreeView')
        #(dither_i,model,itr) = self.FindTreeSelection('DithersTreeView')
        (obsplan_i,model,itr) = self.FindTreeSelection('ObsPlanTreeView')

        targlist_i = self.plan.targets.index(self.plan.activities[int(obsplan_i)].target)
        tellist_i = self.plan.telConfigs.index(self.plan.activities[int(obsplan_i)].telConfig)
        instlist_i = self.plan.instConfigs.index(self.plan.activities[int(obsplan_i)].instConfig)
        dithlist_i = self.plan.dithers.index(self.plan.activities[int(obsplan_i)].dither)

        selection = self.widgets['TargetsTreeView'].get_selection()
        selection.select_path((targlist_i,))
        selection = self.widgets['TelTreeView'].get_selection()
        selection.select_path((tellist_i,))
        selection = self.widgets['ComicsTreeView'].get_selection()
        selection.select_path((instlist_i,))
        selection = self.widgets['DithersTreeView'].get_selection()
        selection.select_path((dithlist_i,))

        self.updateToolArea()
        self.updateTargetSpec()
        self.updateTelConfigSpec()
        self.updateInstConfigSpec()
        self.updateDitherSpec()
        self.updateActivitySpec()



## File and Menu stuff #############################

    def updateToolArea(self):
        self.logger.debug("updateToolArea called")
        selected_target = self.widgets['TargetsTreeView'].get_selection()
        selected_telconfig = self.widgets['TelTreeView'].get_selection()
        selected_instConfig = self.widgets['ComicsTreeView'].get_selection()
        selected_dither = self.widgets['DithersTreeView'].get_selection()
        (model,itr_target)  = selected_target.get_selected()
        (model,itr_telconfig)  = selected_telconfig.get_selected()
        (model,itr_instConfig)  = selected_instConfig.get_selected()
        (model,itr_dither)  = selected_dither.get_selected()
        #
        #print itr_target, itr_telconfig, itr_instConfig, itr_dither
        if itr_target and itr_telconfig and itr_instConfig and itr_dither:
          self.widgets['MakeActivity'].set_sensitive(True)
        else:  # don't enable make activity unless 4 selections
          self.widgets['MakeActivity'].set_sensitive(False)
        self.widgets['oAcctEntry'].set_text(self.plan.oAcct)
        if self.widgets['connect_to_server'].active:
           self.widgets['oAcctPasswordLabel'].set_sensitive(True)
           self.widgets['oAcctPasswordEntry'].set_sensitive(True)
        else:
           self.widgets['oAcctPasswordLabel'].set_sensitive(False)
           self.widgets['oAcctPasswordEntry'].set_sensitive(False)

    def cb_connect_to_server(self, *args):
        self.updateToolArea()
        
    def cb_SaveObsPlanAs(self, *args):
        self.logger.debug("cb_SaveObsPlanAs was called!!!!!")
        chooser = gtk.FileChooserDialog(title="Save as...",
                           action=gtk.FILE_CHOOSER_ACTION_SAVE,
                           buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
          self.filename = chooser.get_filename()
          print self.filename, 'selected'
          plan.WritePlanFile(self.filename,self.plan)
        elif response == gtk.RESPONSE_CANCEL:
          print 'Closed, no files selected'
        chooser.destroy()

    def cb_SaveObsPlan(self, *args):
        self.logger.debug("cb_SaveObsPlan was called!!!!!")
        if self.filename == None:
          self.cb_SaveObsPlanAs(*args)
        else:  # a filename exists to save to
          print self.filename, 'selected'
          plan.WritePlanFile(self.filename,self.plan)
        #


    def cb_OpenObsplan(self, *args):
        self.logger.debug("cb_OpenObsPlan was called!!!!!")
        chooser = gtk.FileChooserDialog("Open...",
                     action=gtk.FILE_CHOOSER_ACTION_OPEN,
                     buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                              gtk.STOCK_OPEN,gtk.RESPONSE_OK))

        afilter = gtk.FileFilter()
        afilter.set_name("Spot files")
        afilter.add_pattern("*.spot")
        chooser.add_filter(afilter)

        afilter = gtk.FileFilter()
        afilter.set_name("All files")
        afilter.add_pattern("*")
        chooser.add_filter(afilter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
          self.filename = chooser.get_filename()
          print self.filename, 'selected'
          self.plan = plan.ReadPlanFile(self.filename)
          self.updateGUI()
        elif response == gtk.RESPONSE_CANCEL:
          print 'Closed, no files selected'
        chooser.destroy()

    def cb_MakeOPEFileAs(self, *args):
        self.logger.debug("cb_MakeOPEFileAs was called!!!!!")
        chooser = gtk.FileChooserDialog(title="Make OPE file as...",
                           action=gtk.FILE_CHOOSER_ACTION_SAVE,
                           buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_EXECUTE,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
          self.opefilename = chooser.get_filename()
          print self.opefilename, 'selected'
          (i, model, itr) = self.FindTreeSelection('ObsPlanTreeView')
          if itr == None:
            print "You must select an activity to make an OPE file!"
          else:  # make the opefile
            oAcct = None
            if self.widgets['connect_to_server'].active:
              oAcct = self.plan.oAcct
            passwd = self.widgets['oAcctPasswordEntry'].get_text()
            #
            self.plan.activities[int(i)].MakeOPEFile(open(self.opefilename,'w'),
                                                                   'TIMESTAMP',
                                                                        oAcct,
                                                                        passwd)
          #
        elif response == gtk.RESPONSE_CANCEL:
          print 'Closed, no files selected'
        chooser.destroy()

    def cb_MakeOPEFile(self, *args):
        if self.opefilename == None:
          self.cb_MakeOPEFileAs(*args)
        else:  # a filename exists to save to
          (i, model, itr) = self.FindTreeSelection('ObsPlanTreeView')
          if itr == None:
            print "You must select an activity to make an OPE file!"
          else:  # make the opefile
            oAcct = None
            if self.widgets['connect_to_server'].active:
              oAcct = self.plan.oAcct
            #
            passwd = self.widgets['oAcctPasswordEntry'].get_text()
            self.plan.activities[int(i)].MakeOPEFile(open(self.opefilename,'w'),
                                                                   'TIMESTAMP',
                                                                        oAcct,
                                                                        passwd)
          #
        #

    def cb_HelpAbout(self, *args):
        print "cb_HelpAbout called"
        dialog = gtk.Dialog()
        label = gtk.Label("\nSee spot.html for help.\n")
        dialog.vbox.pack_start(label, True, True, 0)
        label.show()
        dialog.show()
        print """
        """

    def cb_main_quit( self, *args ):
        #print "cb_main_quit was called!!!!!"
        gtk.main_quit()


#-- Updates --------------------------------------------------------------

    def updateGUI(self):
        self.logger.debug("Update GUI")
        self.updateToolArea()
        self.updateTargetList()
        self.updateTelConfigList()
        self.updateInstConfigList()
        self.updateDitherList()
        self.updateActivityList()
        self.updateTargetSpec()
        self.updateTelConfigSpec()
        self.updateInstConfigSpec()
        self.updateDitherSpec()
        self.updateActivitySpec()
        #print repr(self.plan)

    def updateTargetList(self):
        self.logger.debug("updateTargetList")
        self.targetsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        for i,target in enumerate(self.plan.targets):
            itr = self.targetsListStore.append()
            self.targetsListStore.set( itr,
                COLUMN_ID, i,
                COLUMN_NAME, target.name )
        self.widgets['TargetsTreeView'].set_model(self.targetsListStore)

    def updateTelConfigList(self):
        self.logger.debug("updateTelConfigList")
        self.telConfigsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        for i,telConfig in enumerate(self.plan.telConfigs):
            itr = self.telConfigsListStore.append()
            self.telConfigsListStore.set( itr,
                COLUMN_ID, i,
                COLUMN_NAME, telConfig.name )
        self.widgets['TelTreeView'].set_model(self.telConfigsListStore)

    def updateInstConfigList(self):
        self.logger.debug("updateInstConfigList")
        self.instConfigsListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                    gobject.TYPE_STRING )
        for i,instConfig in enumerate(self.plan.instConfigs):
            itr = self.instConfigsListStore.append()
            self.instConfigsListStore.set( itr,
                COLUMN_ID, i,
                COLUMN_NAME, instConfig.name )
        self.widgets['ComicsTreeView'].set_model(self.instConfigsListStore)

    def updateDitherList(self):
        self.logger.debug("updateDitherList")
        self.dithersListStore = gtk.ListStore(  gobject.TYPE_UINT,
                                                gobject.TYPE_STRING )
        for i,dither in enumerate(self.plan.dithers):
            itr = self.dithersListStore.append()
            self.dithersListStore.set( itr,
                COLUMN_ID, i,
                COLUMN_NAME, dither.name )
        self.widgets['DithersTreeView'].set_model(self.dithersListStore)

    def updateOffsetsList(self):
        self.logger.debug("updateOffsetsList")
        selected = self.widgets['DithersTreeView'].get_selection()
        #print "in updateOffsetsList selected =",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          pass
        else:  # a valid selection
          (dither_i,) = model.get(itr, 0)
          #print dither_i
        selection = self.widgets['OffsetsTreeView'].get_selection()
        #print "in updateOffsetsList selected =",selected
        (model_offset,itr_offset)  = selection.get_selected()
        #print model,itr
        if itr_offset == None:
          offset_i = 0
        else:  # a valid selection
          (offset_i,) = model_offset.get(itr_offset, 0)
          #print dither_i
        self.offsetsListStore.clear()
        for i,offset in enumerate(self.plan.dithers[int(dither_i)].offsets):
            itr = self.offsetsListStore.append()
            self.offsetsListStore.set( itr,
                COLUMN_OFFSET_ID, i,
                COLUMN_OFFSET_RA, offset[0],
                COLUMN_OFFSET_DEC, offset[1] )
        self.widgets['OffsetsTreeView'].set_model(self.offsetsListStore)
        #print 444,offset_i
        selection.select_path(str(offset_i))

    def updateActivityList(self):
        self.logger.debug("updateActivityList")
        (activity_i,model,activity_itr) = self.FindTreeSelection('ObsPlanTreeView')
        selection = self.widgets['ObsPlanTreeView'].get_selection()
        #self.ObsPlanListStore = gtk.ListStore(  gobject.TYPE_UINT,
        #      gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING )
        
        self.ObsPlanListStore.clear()
        for i,activity in enumerate(self.plan.activities):
            itr = self.ObsPlanListStore.append()
            self.ObsPlanListStore.set( itr,
                COLUMN_ID, i,
                COLUMN_ACTNAME, activity.name,
                COLUMN_ACTTAG, activity.tag,
                COLUMN_ACTSTATUS, activity.status )
        self.widgets['ObsPlanTreeView'].set_model(self.ObsPlanListStore)
        if activity_itr != None:
          #print activity_i
          selection.select_path(str(activity_i))


    def updateTargetSpec(self):
        self.logger.debug("updateTargetSpec called")
        selected = self.widgets['TargetsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          self.widgets['TargetIDLabel'].set_text(ID_LABEL%'')
          self.widgets['TargetNameEntry'].set_text('')
          self.widgets['TargetRAEntry'].set_text('')
          self.widgets['TargetDecEntry'].set_text('')
          combobox = self.widgets['TargetEquinoxSelection']
          #model = combobox.get_model()
          active = combobox.set_active(-1)
          combobox = self.widgets['TargetStyleSelection']
          #model = combobox.get_model()
          active = combobox.set_active(-1)
          sensitivity = False
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          target = self.plan.targets[int(i)]
          self.widgets['TargetIDLabel'].set_text(ID_LABEL%i)
          self.widgets['TargetNameEntry'].set_text(target.name)
          self.widgets['TargetRAEntry'].set_text(target.ra)
          self.widgets['TargetDecEntry'].set_text(target.dec)
          combobox = self.widgets['TargetEquinoxSelection']
          #model = combobox.get_model()
          combobox.set_active(plan.Target.TARGET_EQUINOX[target.equinox])
          #
          combobox = self.widgets['TargetStyleSelection']
          #model = combobox.get_model()
          #print TARGET_STYLES[target.equinox]
          combobox.set_active(plan.Target.TARGET_STYLE[target.style])
          sensitivity = True
        for item in ('IDLabel','NameEntry', 'NameLabel',#?'CommentEntry','CommentLabel',
                     'RALabel','RAEntry','DecLabel','DecEntry',
                     'EquinoxLabel','EquinoxSelection','StyleLabel','StyleSelection'):
          self.widgets['Target'+item].set_sensitive(sensitivity)


    def on_TargetEquinoxSelection_changed(self, *args):
        self.logger.debug("on_TargetEquinoxSelection_changed called")

        selected = self.widgets['TargetsTreeView'].get_selection()
        #print "args = ",args
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print "model,itr = ", model,itr
        if itr == None:
          combobox = self.widgets['TargetEquinoxSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(TARGEQUINOX[])
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['TargetEquinoxSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          #print active_index
          self.plan.targets[int(i)].equinox = plan.Target.TARGET_EQUINOX_STRS[active_index]
        self.updateTargetSpec()

    def on_TargetStyleSelection_changed(self, *args):
        self.logger.debug("on_TargetStyleSelection_changed called")

        selected = self.widgets['TargetsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['TargetStyleSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['TargetStyleSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.targets[int(i)].style = plan.Target.TARGET_STYLE_STRS[active_index]


    ditherWidgets = ('DitherIDLabel',
            'DithNameLabel',
            'DithNameEntry',
            #?'DithCommentLabel',
            #?'DithCommentEntry',
            'PosAdjustcheck',
            'RepeatSpinLabel',
            'RepeatSpin',
            'UseDitheringCheck',
            'AddOriginButton',
            'AddOffsetButton',
            'MoveOffsetUpButton',
            'MoveOffsetDownButton',
            'DeleteOffsetButton',
            'OffsetsTreeView',
            'DitherOffsetsLabel',)
    def updateDitherSpec(self):
        self.logger.debug("updateDitherSpec called")
        selected = self.widgets['DithersTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          self.widgets['DitherIDLabel'].set_text(ID_LABEL%'')
          self.widgets['DithNameEntry'].set_text('')
          #self.widgets['UseGuidingcheck'].set_active()
          for item in Spot.ditherWidgets:
            self.widgets[item].set_sensitive(False)
        else:  # a valid selection
          # it is easier tor dither to turn them back on explicitly
          #for item in Spot.ditherWidgets:
          #  self.widgets[item].set_sensitive(True)
          (i,) = model.get(itr, 0)
          #print i
          dither = self.plan.dithers[int(i)]
          self.widgets['DitherIDLabel'].set_text(ID_LABEL%i)
          self.widgets['DitherIDLabel'].set_sensitive(True)
          self.widgets['DithNameLabel'].set_sensitive(True)
          self.widgets['DithNameEntry'].set_sensitive(True)
          self.widgets['DithNameEntry'].set_text(dither.name)
          #?self.widgets['DithCommentLabel'].set_sensitive(True)
          #?self.widgets['DithCommentEntry'].set_sensitive(True)
          self.widgets['PosAdjustcheck'].set_active(dither.pos_adjust)
          self.widgets['PosAdjustcheck'].set_sensitive(True)
          self.widgets['RepeatSpinLabel'].set_sensitive(True)
          self.widgets['RepeatSpin'].set_sensitive(True)
          self.widgets['RepeatSpin'].set_value(dither.repeat)
          self.widgets['UseDitheringCheck'].set_active(dither.use_dithering)
          self.widgets['UseDitheringCheck'].set_sensitive(True)
          self.updateOffsetsList()
          if dither.use_dithering == True:
            self.widgets['DitherOffsetsLabel'].set_sensitive(True)
            self.widgets['OffsetsTreeView'].set_sensitive(True)
            self.widgets['AddOriginButton'].set_sensitive(True)
            self.widgets['AddOffsetButton'].set_sensitive(True)
            selected = self.widgets['OffsetsTreeView'].get_selection()
            #print "selected",selected
            (model,itr)  = selected.get_selected()
            #print model,itr
            if itr != None:  # there is a selection and you could delete it
              self.widgets['MoveOffsetUpButton'].set_sensitive(True)
              self.widgets['MoveOffsetDownButton'].set_sensitive(True)
              self.widgets['DeleteOffsetButton'].set_sensitive(True)
            else:
              self.widgets['MoveOffsetUpButton'].set_sensitive(False)
              self.widgets['MoveOffsetDownButton'].set_sensitive(False)
              self.widgets['DeleteOffsetButton'].set_sensitive(False)
            # end if there is an offsets selection and you could delete it
          else:  # not doing dithering
            self.widgets['DitherOffsetsLabel'].set_sensitive(False)
            self.widgets['OffsetsTreeView'].set_sensitive(False)
            self.widgets['AddOriginButton'].set_sensitive(False)
            self.widgets['AddOffsetButton'].set_sensitive(False)
            self.widgets['MoveOffsetUpButton'].set_sensitive(False)
            self.widgets['MoveOffsetDownButton'].set_sensitive(False)
            self.widgets['DeleteOffsetButton'].set_sensitive(False)
          
          # end if using dithering
        #  end else a valid dither selection
        



    telConfigWidgets = ('TelIDLabel','TelNameEntry', 'TelNameLabel',
                        #?'TelCommentEntry','TelCommentLabel',
                        'ChoppingLabel','DefChopPAcheck','UseNoddingcheck',
                        'DefNodPAcheck','NodThrowLabel','NodPALabel',
                        'NodThrowEntry','NodPAEntry','ChopThrowLabel',
                        'ChopThrowEntry','ChopPAEntry','ChopPALabel',
                        'TelInstPALabel','TelInstPAEntry',
                        'UseGuidingcheck','TelYOffsetLabel',
                        'TelYOffsetEntry','TelXOffsetLabel',
                        'TelXOffsetEntry','TelOffsetLabel',
                        'TelGraphArea','TelGraphLabel',)
    def updateTelConfigSpec(self):
        self.logger.debug("updateTelConfigSpec called")
        selected = self.widgets['TelTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          for item in Spot.telConfigWidgets:
            self.widgets[item].set_sensitive(False)
        else:  # a valid selection
          for item in Spot.telConfigWidgets:
            self.widgets[item].set_sensitive(True)
          (i,) = model.get(itr, 0)
          #print i
          telConfig = self.plan.telConfigs[int(i)]
          self.widgets['TelIDLabel'].set_text(ID_LABEL%i)
          self.widgets['TelNameEntry'].set_text(telConfig.name)
          self.widgets['ChopThrowEntry'].set_text(str(telConfig.chop.throw))
          self.widgets['DefChopPAcheck'].set_active(telConfig.chop.use_def_pa)
          if True == telConfig.chop.use_def_pa:  # use def so grey out
            self.widgets['ChopPAEntry'].set_sensitive(False)
            self.widgets['ChopPALabel'].set_sensitive(False)
          else:  # show the value
            self.widgets['ChopPAEntry'].set_text(str(telConfig.chop.pa))
          #
          self.widgets['UseNoddingcheck'].set_active(telConfig.use_nodding)
          if True == telConfig.use_nodding:  # a nodding obs
            self.widgets['NodThrowEntry'].set_text(str(telConfig.nod.throw))
            self.widgets['DefNodPAcheck'].set_active(telConfig.nod.use_def_pa)
            if True == telConfig.nod.use_def_pa:  # use def so grey out
              self.widgets['NodPAEntry'].set_sensitive(False)
              self.widgets['NodPALabel'].set_sensitive(False)
            else:  # show the value
              self.widgets['NodPAEntry'].set_text(str(telConfig.nod.pa))
            #
          else:  # not a nodding obs
            self.widgets['NodThrowEntry'].set_sensitive(False)
            self.widgets['NodThrowLabel'].set_sensitive(False)
            self.widgets['DefNodPAcheck'].set_sensitive(False)
            self.widgets['NodPAEntry'].set_sensitive(False)
            self.widgets['NodPALabel'].set_sensitive(False)
          #
          self.widgets['TelInstPAEntry'].set_text(str(telConfig.inst_pa))
          self.widgets['TelXOffsetEntry'].set_text(str(telConfig.offset[0]))
          self.widgets['TelYOffsetEntry'].set_text(str(telConfig.offset[1]))
          self.widgets['UseGuidingcheck'].set_active(telConfig.use_autoguide)
          #print self.widgets['TelGraphArea']
          self.widgets['TelGraphArea'].set_sensitive(True)
          self.on_TelGraphArea_expose_event()

    def drawCircle(self,cx,cy,radius):
        self.logger.debug("draw circle at %s %s %s" % (cx,cy,radius))
        left = int((cx-radius) * self.arc2screen) + self.center_x
        top = int((cy-radius) * self.arc2screen) + self.center_y
        width = int(radius * 2 * self.arc2screen)
        height = int(radius * 2 * self.arc2screen)
        self.drawable.draw_arc(self.gc, False, left, top, width, height, 0, 360*64)
        #return(left, top, width, height)
        
    def drawRect(self,cx,cy,width,height,fill=False):
        self.logger.debug("Draw rect %s,%s %sx%s %s" % (cx,cy,width,height,fill))
        left = int((cx-(width/2.0)) * self.arc2screen) + self.center_x
        top = int((cy-(height/2.0)) * self.arc2screen) + self.center_y
        width = int(width * self.arc2screen)
        height = int(height * self.arc2screen)
        self.drawable.draw_rectangle(self.gc, fill, left, top, width, height)
        return(left, top, width, height)
        
    def drawLine(self,x0,y0,x1,y1):
        self.logger.debug("Draw line from %s,%s to %s,%s" % (x0,y0,x1,y1))
        x0 = int(x0 * self.arc2screen) + self.center_x
        y0 = int(y0 * self.arc2screen) + self.center_y
        x1 = int(x1 * self.arc2screen) + self.center_x
        y1 = int(y1 * self.arc2screen) + self.center_y
        self.drawable.draw_line(self.gc, x0,y0,x1,y1)
        return(x0,y0,x1,y1)

    def drawText(self,x,y,text):
        self.pangolayout.set_text(text)
        (xsize,ysize) = self.pangolayout.get_pixel_size()
        self.logger.debug("Draw text at %s,%s %s" % (x,y,text))
        x = int(x * self.arc2screen) + self.center_x - xsize/2
        y = int(y * self.arc2screen) + self.center_y - ysize/2
        self.widgets['TelGraphArea'].window.draw_layout(self.gc,x,y, self.pangolayout)
        
    #color = gtk.gdk.color_parse('red')
    def on_TelGraphArea_expose_event(self, *args):
        self.logger.debug("on_TelGraphArea_expose_event")
        selected = self.widgets['TelTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          pass
        else:  # a valid selection
          #for item in Spot.telConfigWidgets:
          #  self.widgets[item].set_sensitive(True)
          (tellist_i,) = model.get(itr, 0)
          tellist_i = int(tellist_i)
          #print self.widgets['TelGraphArea']
          #self.widgets['TelGraphArea'].set_size_request(100,100)

          self.widgets['TelGraphArea'].realize()

          #self.widgets['TelGraphArea'].modify_bg(gtk.STATE_NORMAL,self.color)
          self.drawable = self.widgets['TelGraphArea'].window
          self.widgets['TelGraphArea'].window.clear()
          (t,t,x,y,t) = self.widgets['TelGraphArea'].window.get_geometry()
          self.windowheight = y-1
          self.windowwidth = y   #* 4.0 / 3.0
          self.center_y = self.windowheight / 2
          self.center_x = self.windowwidth / 2
          
          #self.style = self.widgets['TelGraphArea'].get_style()
          #self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
          #self.gc = self.style.fg_gc[gtk.STATE_STIPLLED]
          #self.gc = self.drawable.new_gc()  #fill=gtk.gdk.STIPPLED)

          self.arc2screen = 2.0
          self.buffer = 5
          self.label = 20

          #print drawable
          self.gc = self.drawable.new_gc()

          #self.drawable.draw_rectangle(self.gc, False, self.buffer, self.buffer,
          #                              self.windowwidth-(self.buffer*2),
          #                              self.windowheight-(self.buffer*2))

          axisscale = 32
          headingscale = 1.1
          nx = -math.sin(math.radians(90+float(self.plan.telConfigs[tellist_i].inst_pa))) * axisscale
          ny = -math.cos(math.radians(90+float(self.plan.telConfigs[tellist_i].inst_pa))) * axisscale
          sx = -nx
          sy = -ny
          ex =  math.sin(math.radians(   float(self.plan.telConfigs[tellist_i].inst_pa))) * axisscale
          ey =  math.cos(math.radians(   float(self.plan.telConfigs[tellist_i].inst_pa))) * axisscale
          wx = -ex
          wy = -ey
          
          self.drawLine(nx,ny,sx,sy)
          self.drawLine(ex,ey,wx,wy)

          
          self.pangolayout = self.widgets['TelGraphArea'].create_pango_layout("")
          self.drawText(nx*headingscale, ny*headingscale, "N")
          self.drawText(sx*headingscale, sy*headingscale, "S")
          self.drawText(ex*headingscale, ey*headingscale, "E")
          self.drawText(wx*headingscale, wy*headingscale, "W")


          self.drawRect(0, 0, 40, 30)  # detector
          #?self.drawRect(0, 0, 40-2,  1, False)  # slit




          self.logger.debug("tellist_i %s" % tellist_i)
          self.logger.debug("chop.use_def_pa %s" % self.plan.telConfigs[tellist_i].chop.use_def_pa)
          self.logger.debug("inst_pa %s" % self.plan.telConfigs[tellist_i].inst_pa)
          self.logger.debug("chop.pa %s" % self.plan.telConfigs[tellist_i].chop.pa)
          self.logger.debug("nod.use_def_pa %s" % self.plan.telConfigs[tellist_i].nod.use_def_pa)
          self.logger.debug("nod.pa %s" % self.plan.telConfigs[tellist_i].nod.pa)
          self.logger.debug("chop.throw %s" % self.plan.telConfigs[tellist_i].chop.throw)
          self.logger.debug("nod.throw %s" % self.plan.telConfigs[tellist_i].nod.throw)
          self.logger.debug("offset x %s" % self.plan.telConfigs[tellist_i].offset[0])
          self.logger.debug("offset y %s" % self.plan.telConfigs[tellist_i].offset[1])



          #print 99,self.plan.telConfigs[tellist_i].chop.pa
          #print 88,math.radians(float(self.plan.telConfigs[tellist_i].chop.pa))
          #print 77,math.cos(math.radians(float(self.plan.telConfigs[tellist_i].chop.pa)))
          
          if self.plan.telConfigs[tellist_i].chop.use_def_pa == True:
            choppa = -1.0 * float(self.plan.telConfigs[tellist_i].inst_pa)
          else:  # use real chop pa
            choppa = float(self.plan.telConfigs[tellist_i].chop.pa)
          #
          if self.plan.telConfigs[tellist_i].nod.use_def_pa == True:
            nodpa = -1.0 * float(self.plan.telConfigs[tellist_i].inst_pa)
          else:  # use real chop pa
            nodpa = float(self.plan.telConfigs[tellist_i].nod.pa)
          #
          self.logger.debug("choppa %s" % choppa)
          self.logger.debug("nodpa %s" % nodpa)
          self.logger.debug("chopthrow %s" % self.plan.telConfigs[tellist_i].chop.throw)
          self.logger.debug("chopthrow %r" % self.plan.telConfigs[tellist_i].chop.throw)

          chopx = float(self.plan.telConfigs[tellist_i].chop.throw)
          chopx *= (math.sin(math.radians(choppa + 90.0 + float(self.plan.telConfigs[tellist_i].inst_pa) )))
          chopy = float(self.plan.telConfigs[tellist_i].chop.throw) * (
                        math.cos(math.radians(choppa + 90 + 
                                              float(self.plan.telConfigs[tellist_i].inst_pa) )))
          nodx = float(self.plan.telConfigs[tellist_i].nod.throw) * (
                        math.sin(math.radians(nodpa + 90 + 
                                              float(self.plan.telConfigs[tellist_i].inst_pa) )))
          nody = float(self.plan.telConfigs[tellist_i].nod.throw) * (
                        math.cos(math.radians(nodpa +90 + 
                                              float(self.plan.telConfigs[tellist_i].inst_pa) )))

          c0x = float(self.plan.telConfigs[tellist_i].offset[0])
          c0y = float(self.plan.telConfigs[tellist_i].offset[1])

          #? put these calcs and conversions in the model, but not zoom and gtk_offset
          c1x = c0x + chopx
          c1y = c0y + chopy
          n0x = c0x + nodx
          n0y = c0y + nody
          n1x = c0x + chopx + nodx
          n1y = c0y + chopy + nody

          self.drawRect(c0x, c0y, 1,1)
          self.drawRect(c1x, c1y, 2,2)
          if self.plan.telConfigs[tellist_i].use_nodding:
            self.drawCircle(n0x, n0y, 1)
            self.drawCircle(n1x, n1y, 1.5)
          
          # measurement circles
          #for r in range(10,100,10):
          #  self.drawCircle(c0x, c0y, r)
        # end else valid selection
    # end on_TelGraphArea_expose_event()



    instConfigWidgets = ('ComicsIDLabel',
            'ComicsNameLabel',
            'ComicsNameEntry',
            #?'ComicsCommentLabel',
            #?'ComicsCommentEntry',
            'ReadoutPriorityLabel',
            'ReadoutPrioritySelection',
            'IntegTimeLabel',
            'IntegTimeEntry',
            'SlitWidthLabel',
            'SlitWidthSelection',
            'CentralWavelengthLabel',
            'CentralWavelengthEntry',
            'SetDefCentralWavelengthButton',
            'ImagingFilterLabel',
            'ImagingFilterSelection',
            'ComicsModeLabel',
            'ComicsModeSelection',
            'DetectorsLabel',
            'DetectorImgLabel',
            'DetectorSpc1Label',
            'detectorSpc2Label',
            'label72',
            'label73',
            'ImgButton',
            'Spc11Button',
            'Spc15Button',
            'Spc14Button',
            'Spc13Button',
            'Spc12Button',
            'Spc25Button',
            'Spc24Button',
            'Spc23Button',
            'Spc22Button',
            'Spc21Button',)
    detButtons = ('ImgButton',
            'Spc11Button',
            'Spc15Button',
            'Spc14Button',
            'Spc13Button',
            'Spc12Button',
            'Spc25Button',
            'Spc24Button',
            'Spc23Button',
            'Spc22Button',
            'Spc21Button',)
    def updateInstConfigSpec(self):
        self.logger.debug("updateInstConfigSpec called")
        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        for button in Spot.detButtons:
          self.widgets[button].modify_bg(gtk.STATE_NORMAL,DETECTOR_NOTUSED)
        #
        if itr == None:
          self.widgets['ComicsIDLabel'].set_text(ID_LABEL%'')
          self.widgets['ComicsNameEntry'].set_text('')
          self.widgets['IntegTimeEntry'].set_text('')
          self.widgets['CentralWavelengthEntry'].set_text('')
          for item in Spot.instConfigWidgets:
            self.widgets[item].set_sensitive(False)
        else:  # a valid selection
          for item in Spot.instConfigWidgets:
            self.widgets[item].set_sensitive(True)
          (i,) = model.get(itr, 0)
          #print i
          instConfig = self.plan.instConfigs[int(i)]
          self.widgets['ComicsIDLabel'].set_text(ID_LABEL%i)
          self.widgets['ComicsNameEntry'].set_text(instConfig.name)
          self.widgets['IntegTimeEntry'].set_text(str(instConfig.integ_time_per_beam))
          if instConfig.mode == "IMG_N" or instConfig.mode == "IMG_Q":
            self.widgets['CentralWavelengthLabel'].set_sensitive(False)
            self.widgets['CentralWavelengthEntry'].set_text('')
            self.widgets['CentralWavelengthEntry'].set_sensitive(False)
            self.widgets['SetDefCentralWavelengthButton'].set_sensitive(False)
          else:  # show central
            self.widgets['CentralWavelengthEntry'].set_text(str(instConfig.center_wavelength))
          #
          combobox = self.widgets['ReadoutPrioritySelection']
          combobox.set_active(comics.InstConfig.READOUT_PRIORITY[
                                                 instConfig.readout_priority])
          combobox = self.widgets['SlitWidthSelection']
          combobox.set_active(comics.InstConfig.SLIT_WIDTH[
                                                 instConfig.slit_width])
          combobox = self.widgets['ComicsModeSelection']
          combobox.set_active(comics.COMICS_MODE[instConfig.mode])
          combobox = self.widgets['ImagingFilterSelection']
          combobox.set_active(
                   comics.COMBO[instConfig.mode].index(instConfig.img_filter))
          row = comics.Detector().getRowByModeFilter(instConfig.mode,
                                                     instConfig.img_filter)
          if "1" == row.dispDet[0]:
            self.widgets['ImgButton'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )

          if "1" == row.dispDet[1]:
            self.widgets['Spc11Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
          if "2" == row.dispDet[1]:
            self.widgets['Spc11Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
            self.widgets['Spc21Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )

          if "1" == row.dispDet[2]:
            self.widgets['Spc12Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
          if "2" == row.dispDet[2]:
            self.widgets['Spc12Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
            self.widgets['Spc22Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )

          if "1" == row.dispDet[3]:
            self.widgets['Spc13Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
          if "2" == row.dispDet[3]:
            self.widgets['Spc13Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
            self.widgets['Spc23Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )

          if "1" == row.dispDet[4]:
            self.widgets['Spc14Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
          if "2" == row.dispDet[4]:
            self.widgets['Spc14Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
            self.widgets['Spc24Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )

          if "1" == row.dispDet[5]:
            self.widgets['Spc15Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
          if "2" == row.dispDet[5]:
            self.widgets['Spc15Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )
            self.widgets['Spc25Button'].modify_bg(gtk.STATE_NORMAL, DETECTOR_USED )



    def on_ReadoutPrioritySelection_changed(self, *args):
        self.logger.debug("on_ReadoutPrioritySelection_changed called")

        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['ReadoutPrioritySelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['ReadoutPrioritySelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.instConfigs[int(i)].readout_priority = \
                          comics.InstConfig.READOUT_PRIORITY_STRS[active_index]

    def on_ComicsModeSelection_changed(self, *args):
        self.logger.debug("on_ComicsModeSelection_changed called")

        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['ComicsModeSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['ComicsModeSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.instConfigs[int(i)].mode = \
                          comics.COMICS_MODE_STRS[active_index]
          # comics Imaging filter
          combobox2 = self.widgets['ImagingFilterSelection']
          for j in range(len(comics.img_filter_defs)):  # max possible length
            combobox2.remove_text(0)
          # end for remove max possible img filter entries
          for j,string in enumerate(comics.COMBO[self.plan.instConfigs[int(i)].mode]):
            combobox2.append_text(string)
          # end for add all appropriate entries for this mode
          combobox2.set_active(0)
          # set central wavelength
          self.widgets['CentralWavelengthEntry'].set_text(
               comics.CENTRAL_WAVELENGTH[self.plan.instConfigs[int(i)].mode])
          self.updateInstConfigSpec()



    def on_ImagingFilterSelection_changed(self, *args):
        self.logger.debug("on_ComicsModeSelection_changed called")

        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['ImagingFilterSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['ImagingFilterSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.instConfigs[int(i)].img_filter = \
                 comics.COMBO[self.plan.instConfigs[int(i)].mode][active_index]


    def on_SlitWidthSelection_changed(self, *args):
        self.logger.debug("on_SlitWidthSelection_changed called")

        selected = self.widgets['ComicsTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['SlitWidthSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['SlitWidthSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.instConfigs[int(i)].slit_width = \
                          comics.InstConfig.SLIT_WIDTH_STRS[active_index]


    def on_ActivityStatusSelection_changed(self, *args):
        self.logger.debug("on_ActivityStatusSelection_changed called")

        selected = self.widgets['ObsPlanTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          combobox = self.widgets['ActivityStatusSelection']
          #model = combobox.get_model()
          #active = combobox.set_active(0)
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          combobox = self.widgets['ActivityStatusSelection']
          #model = combobox.get_model()
          active_index = combobox.get_active()
          self.plan.activities[int(i)].status = \
                          comics.Activity.STATUS_STRS[active_index]
          self.updateActivityList()


    def updateActivitySpec(self):
        self.logger.debug("updateActivitySpec called")
        selected = self.widgets['ObsPlanTreeView'].get_selection()
        #print "selected",selected
        (model,itr)  = selected.get_selected()
        #print model,itr
        if itr == None:
          self.widgets['ActivityIDLabel'].set_text(ID_LABEL%'')
          self.widgets['ActivityTagEntry'].set_text('')
          self.widgets['ActivityNameEntry'].set_text('')
          self.widgets['ActivityCommentEntry'].set_text('')

          combobox = self.widgets['ActivityStatusSelection']
          #model = combobox.get_model()
          active = combobox.set_active(-1)
          combobox = self.widgets['ActivityStatusSelection']
          #model = combobox.get_model()
          active = combobox.set_active(-1)

          sensitivity = False
        else:  # a valid selection
          (i,) = model.get(itr, 0)
          #print i
          activity = self.plan.activities[int(i)]
          self.widgets['ActivityIDLabel'].set_text(ID_LABEL%i)
          self.widgets['ActivityTagEntry'].set_text(activity.tag)
          self.widgets['ActivityNameEntry'].set_text(activity.name)
          self.widgets['ActivityCommentEntry'].set_text(activity.comment)
          combobox = self.widgets['ActivityStatusSelection']
          combobox.set_active(comics.Activity.STATUS[activity.status])
          sensitivity = True
        for item in ('IDLabel','TagEntry','TagLabel','NameEntry', 'NameLabel',
                     'CommentLabel','CommentEntry','StatusLabel','StatusSelection'):
          self.widgets['Activity'+item].set_sensitive(sensitivity)



def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('spot', options)

    # evil hack required to use threads with GTK
    gtk.gdk.threads_init()

    w = Spot(logger, filename=options.filename)
    w.show()
    # Process X events
##     while gtk.events_pending():
##         gtk.main_iteration()

##         # Sleep and let other threads run
##         print "Must SLEEP..."
##         time.sleep(0.25)
    gtk.main()


if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="963x1037+0+57",
                      help="X geometry for initial size and placement")
    optprs.add_option("-f", "--filename", dest="filename",
                      metavar="FILE",
                      help="Open FILE for spot tool")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

##     if len(args) != 0:
##         optprs.error("incorrect number of arguments")

    if options.display:
        os.environ['DISPLAY'] = options.display

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

#END
