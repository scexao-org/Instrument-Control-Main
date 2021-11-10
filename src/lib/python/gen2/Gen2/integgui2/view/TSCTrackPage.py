# 
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu May 23 16:16:11 HST 2013
#]

import os, glob
import gtk

import myproc

import common
import CodePage
import cfg.g2soss as g2soss

import astro.jplHorizonsIF as jplHorizonsIF
import astro.TSCTrackFile as TSCTrackFile

class TSCTrackPage(CodePage.CodePage):

    def __init__(self, frame, name, title):

        super(TSCTrackPage, self).__init__(frame, name, title)

        # add a bottom button
        self.btn_copyTSC = gtk.Button("Copy to TSC")
        self.btn_copyTSC.connect("clicked", lambda w: self.copyTSCcb())
        self.btn_copyTSC.show()
        self.leftbtns.pack_end(self.btn_copyTSC)

        self.tscFilePath = None

    def copyTSCcb(self):
        # Copy the TSC-format file to the TSC computer.

        # Create the filename to use on TSC from the proposal ID.
        propID = common.controller.propid
        tscFilename = '.'.join(['%s_nstrack' % propID, 'dat'])
        self.logger.info('tscFilename %s'%tscFilename)
        iconfile = 'Sheep_jumps.gif'
        imagefile = self.get_media(iconfile, subdir='Images')
        soundfile = 'beep-05.au'
        soundfile = self.get_media(soundfile, subdir='Sounds')
        itemlist = [('TSC Filename:', tscFilename)]

        def _soundfn(filename):
            return lambda : common.controller.playSound(filename)

        def _userinput_cb(val, button_vals, d):
            tscFilename = d[itemlist[0][0]]
            if val == button_vals[1]:
                # Copy the *.tsc file to the TSC computer.
                try:
                    tscPath = TSCTrackFile.copyToTSC(self.filepath, tscFilename, self.logger)
                    common.view.popup_info('TSC ephemerides', '%s copied to %s' % (self.filepath, tscPath))

                except Exception as e:
                    return common.view.popup_error("Cannot copy file to TSC: %s" % (
                        str(e)))
            else:
                self.logger.info('Copy to TSC cancelled: %s to %s' % (self.filepath, tscFilename))

        # Ask the user to confirm it is ok to copy file to TSC. This
        # also gives them the opportunity to change the filename if
        # they want to.
        common.view.obs_userinput('mytag', 'Copy tracking coordinate file to TSC?',
                                  imagefile, _soundfn(soundfile),
                                  itemlist, _userinput_cb)

    def get_media(self, mediafile, subdir=None, mediapaths=None):
        if mediafile.startswith('/'):
            return mediafile
        try:
            confhome = g2soss.producthome
        except:
            confhome = os.path.join(os.environ['CONFHOME'], '/product')

        if not mediapaths:
            if not subdir:
                raise Exception("No subdir parameter passed")
            
            mediapaths = [ os.path.join(confhome, 'file', subdir) ]

        for path in mediapaths:
            mediapath = os.path.join(path, mediafile)
            files = glob.glob(mediapath)
            for filepath in files:
                if os.path.exists(filepath):
                    return filepath

        raise Exception("No such media file (%s) found in %s" % (
            mediafile, mediapaths))
#END
