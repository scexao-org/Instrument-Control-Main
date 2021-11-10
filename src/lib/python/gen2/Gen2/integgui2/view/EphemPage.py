# 
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Mar  5 15:26:23 HST 2013
#]

import os, glob
import gtk

import myproc

import common
import CodePage
import TSCTrackPage
import cfg.g2soss as g2soss

import astro.jplHorizonsIF as jplHorizonsIF
import astro.TSCTrackFile as TSCTrackFile

class EphemPage(CodePage.CodePage):

    def __init__(self, frame, name, title):

        super(EphemPage, self).__init__(frame, name, title)

        # add some bottom buttons
        self.btn_convertToTSC = gtk.Button("Convert to TSC format")
        self.btn_convertToTSC.connect("clicked", lambda w: self.convertToTSCcb())
        self.btn_convertToTSC.show()
        self.leftbtns.pack_end(self.btn_convertToTSC)

        self.btn_copyTSC = gtk.Button("Convert and Copy to TSC")
        self.btn_copyTSC.connect("clicked", lambda w: self.copyTSCcb())
        self.btn_copyTSC.show()
        self.leftbtns.pack_end(self.btn_copyTSC)

        self.tscFilePath = None

    def convertToTSC(self):
        # get text to process from the buffer, which should be
        # ephemeris data output from JPL Horizons
        start, end = self.buf.get_bounds()
        buf = self.buf.get_text(start, end)

        # Parse the input buffer to create the JPLHorizonsEphem
        # object.
        jplHorizonsEphem = jplHorizonsIF.JPLHorizonsEphem(buf, self.logger)

        # Make the TSC file path from the filename from which the
        # buffer was filled.
        tscdir, tscfile = os.path.split(self.filepath)
        tscpfx, tscext = os.path.splitext(tscfile)
        self.tscFilePath = os.path.join(tscdir, '%s.tsc' % tscpfx)

        # Write out the tracking coordinates to the TSC file and then
        # read that file back into a text string.
        TSCTrackFile.writeTSCTrackFile(self.tscFilePath, jplHorizonsEphem.trackInfo, self.logger)
        with open(self.tscFilePath, 'r') as f:
            output = f.read()

        # Load the converted tracking coordinates into a new page.
        common.view.open_generic(common.view.exws, output, self.tscFilePath,
                                 TSCTrackPage.TSCTrackPage)

    def convertToTSCcb(self):
        # Convert the input buffer to TSC format and display the
        # results in a new page
        try:
            self.convertToTSC()
        except Exception as e:
            return common.view.popup_error("Cannot convert input to TSC format: %s" % (
                str(e)))

    def copyTSCcb(self):
        # Convert the input buffer to TSC format, display the results
        # in a new page, and copy the TSC-format file to the TSC
        # computer.
        try:
            self.convertToTSC()
        except Exception as e:
            return common.view.popup_error("Cannot convert input to TSC format: %s" % (
                    str(e)))

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
            if val == button_vals[1]:
                tscFilename = d[itemlist[0][0]]
                # Copy the *.tsc file to the TSC computer.
                try:
                    tscPath = TSCTrackFile.copyToTSC(self.tscFilePath, tscFilename, self.logger)
                    common.view.popup_info('TSC ephemerides', '%s copied to %s' % (self.tscFilePath, tscPath))

                except Exception as e:
                    return common.view.popup_error("Cannot copy file to TSC: %s" % (
                        str(e)))
            else:
                self.logger.info('Copy to TSC cancelled: %s to %s' % (self.tscFilePath, d['TSC Filename']))

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
