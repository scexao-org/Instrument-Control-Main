#
# HandsetPage.py -- implements an Integgui2 handset
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Oct 22 21:23:45 HST 2010
#]

import gtk
import pango

import yaml

import common
import Page
import CommandObject

import Bunch
        
compass_template = """
  %(n)s
%(e)s + %(w)s
  %(s)s
"""

class HandsetError(Exception):
    pass

class HandsetPage(Page.CommandPage):

    def __init__(self, frame, name, title):

        super(HandsetPage, self).__init__(frame, name, title)

        self.queueName = 'launcher'
        self.tm_queueName = 'launcher'
        self.paused = False

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        lw = gtk.Layout()
        lw.set_size(420, 340)
        scrolled_window.add(lw)
        lw.show()
        scrolled_window.show()

        frame.pack_start(scrolled_window, expand=True, fill=True)

        self.lw = lw
        
        self.btn_cancel = gtk.Button("Cancel")
        self.btn_cancel.connect("clicked", lambda w: self.cancel())
        self.btn_cancel.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['cancelbtn'])
        self.btn_cancel.show()
        self.leftbtns.pack_end(self.btn_cancel)

        ## menu = self.add_menu()
        ## self.add_close()
        
        menu = self.add_pulldownmenu("Page")

        # Add items to the menu
        item = gtk.MenuItem(label="Reset")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.reset(),
                             "menu.Reset")
        item.show()

        #self.add_close(side=Page.LEFT)
        #self.add_close()
        item = gtk.MenuItem(label="Close")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

        self.build_handset()


    def _make_compass(self, n, s, e, w):
        txt = compass_template % {'n': n, 's': s, 'e': e, 'w': w }
        lbl = gtk.Label(txt)
        lbl.modify_font(pango.FontDescription('Monospace 11'))
        lbl.show()
        return lbl

    def _make_button(self, name):
        img = gtk.Image()
        # make xpm image from inline data
        try:
            xpm_data = icons[name]
            pixbuf = gtk.gdk.pixbuf_new_from_xpm_data(xpm_data)
            img.set_from_pixbuf(pixbuf)
        except:
            img = gtk.Label(name)

        btn = gtk.Button()
        btn.add(img)
        img.show()
        btn.show()
        return btn
    
    def build_handset(self):
        self.arrow_stepval = 1.0
        
        widgets = {}

        # Place arrow buttons
        off_xv = 220
        off_yh = 150

        btns = widgets.setdefault('buttons', {})
        for x, y, name, axis, mult in ((off_xv, off_yh-140, 'up3', 0, 10),
                                       (off_xv, off_yh-100, 'up2', 0, 3),
                                       (off_xv, off_yh-60, 'up1', 0, 1),
                                       (off_xv-170, off_yh, 'left3', 1, 10),
                                       (off_xv-130, off_yh, 'left2', 1, 3),
                                       (off_xv-90, off_yh, 'left1', 1, 1),
                                       (off_xv+80, off_yh, 'right1', 1, -1),
                                       (off_xv+120, off_yh, 'right2', 1, -3),
                                       (off_xv+160, off_yh, 'right3', 1, -10),
                                       (off_xv, off_yh+60, 'down1', 0, -1),
                                       (off_xv, off_yh+100, 'down2', 0, -3),
                                       (off_xv, off_yh+140, 'down3', 0, -10),
                                 ):
            btn = self._make_button(name)
            btn.connect("clicked", self.arrowMove, axis, mult)
            btns[name] = btn
            self.lw.put(btn, x, y)

        # Place entries
        ents = widgets.setdefault('entries', {})
        for x, y, width, name in ((off_xv-35, off_yh+5, 10, 'mainstep'),):
            ent = gtk.Entry()
            ent.set_alignment(1.0)
            ent.set_text("0")
            ent.set_width_chars(width)
            ent.show()
            ents[name] = ent
            self.lw.put(ent, x, y)

        # Place spin buttons
        for x, y, name in ((20, 250, 'lspin'), (120, 250, 'rspin')):
            ent = gtk.SpinButton()
            ent.show()
            ent.set_alignment(1.0)
            ent.set_update_policy(gtk.UPDATE_ALWAYS)
            # this seems to force size
            ent.set_range(-1000, 1000)
            ents[name] = ent
            self.lw.put(ent, x, y)

        # Place labels
        lbls = widgets.setdefault('labels', {})
        for x, y, txt, name in ((off_xv+45, 210+5, 'x1', 'x1'), (off_xv+45, 250+5, 'x3', 'x3'),
                                (off_xv+45, 290+5, 'x10', 'x10'),
                                (off_xv, off_yh-18, 'Step', 'mainstep'),
                                (off_xv-5, off_yh+35, 'arcsec', 'mainunit'),
                                (20, 30, 'Mode', 'mode'),
                                (20, 232, '+N/-S', 'lstep'),
                                (120, 232, '+E/-W', 'rstep'),
                                (20, 275, 'arcsec', 'lstepunit'),
                                (120, 275, 'arcsec', 'rstepunit')):
            lbl = gtk.Label(txt)
            lbl.show()
            lbls[name] = lbl
            self.lw.put(lbl, x, y)
            
        # Compass
        lbl = self._make_compass('N', 'S', 'E', 'W')
        lbls['compass'] = lbl
        self.lw.put(lbl, off_xv+80, off_yh-120)

        # Place buttons
        btns = widgets['buttons']
        btn = gtk.Button('Move')
        #btn.set_size(10, -1)
        btn.connect("clicked", self.execute)
        btn.show()
        btns['move'] = btn
        self.lw.put(btn, 20, 300)

        # Mode drop-down
        cbox = gtk.combo_box_new_text()
        cbox.show()
        cbox.connect("changed", self.changeMode)
        btns['mode'] = cbox
        self.lw.put(cbox, 20, 50)

        self.widgets = widgets
        
    def reset(self):
        # Reset button backgrounds
        for name in ('left1', 'left2', 'left3', 'up1', 'up2', 'up3',
                     'right1', 'right2', 'right3', 'down1', 'down2',
                     'down3', 'move'):
            btn = self.widgets['buttons'][name]
            btn.modify_bg(gtk.STATE_NORMAL,
                          common.launcher_colors['normal'])

    def addModes(self, modes):
        cbox = self.widgets['buttons']['mode']
        
        # remove old labels
        try:
            for i in xrange(0, 100):
                cbox.remove_text(i)
        except:
            pass

        # add new labels
        self.modes = []
        index = 0
        for d in modes:
            assert isinstance(d, dict) and d.has_key('label'), \
                   HandsetError("Malformed handset mode: expected key 'modes': %s" % (
                str(d)))
            name = d['label']
            cbox.insert_text(index, name)
            self.modes.append(d)
            index += 1
            
        cbox.set_active(0)


    def changeMode(self, w):
        # Combobox widget gives us an index
        i = w.get_active()
        assert i < len(self.modes), Exception("No modes loaded!")

        self.loadMode(self.modes[i])
        return True

    # Example of a mode ################
    ## label: "Default"
    ## stepvalue: 1.0
    ## arrows:
    ##     cmd: MOVETELESCOPE OBE_ID=COMMON OBE_MODE=HANDSET OFFSET_MODE=RELATIVE_ARROW
    ##     dec: [ DELTA_DEC, arcsec, "N", "S", 0 ]
    ##     ra : [  DELTA_RA, arcsec, "E", "W", 0 ]
    ## button:
    ##     cmd: MOVETELESCOPE OBE_ID=COMMON OBE_MODE=HANDSET OFFSET_MODE=RELATIVE
    ##     dec: [ DELTA_DEC, arcsec, "+N", "-S", 0.0 ]
    ##     ra : [  DELTA_RA, arcsec, "+E", "-W", 0.0 ]
    ##
    def loadMode(self, d):
        self.reset()
        self.logger.info("Loading handset mode '%s'" % d['label'])

        try:
            for key in ('arrows', 'button'):
                assert d.has_key(key), \
                       HandsetError("Malformed handset mode: expected key '%s': %s" % (
                    key, str(d)))

            # Process arrow info
            info = d['arrows']
            for key in ('cmd', 'dec', 'ra', 'unit', 'step'):
                assert info.has_key(key), \
                       HandsetError("Malformed handset mode: expected key '%s': %s" % (
                    key, str(info)))

            for key in ('dec', 'ra'):
                tup = info[key]
                assert isinstance(tup, list) and (len(tup) == 3), \
                       HandsetError("Malformed handset mode: key '%s': %s" % (
                    key, str(tup)))

            self.stepval = info['step']

            # Set central entry widget to step value
            mainstep = self.widgets['entries']['mainstep']
            mainstep.set_text(str(self.stepval))
            
            # Get number of decimal places in step value
            s = str(self.stepval)
            if not '.' in s:
                numdigits = 0
            else:
                xx, dec = s.split('.')
                numdigits = len(dec)
                
            # Adjust spin widgets to step value
            lspin = self.widgets['entries']['lspin']
            lspin.set_digits(numdigits)
            lspin.set_increments(self.stepval, self.stepval*3)
            rspin = self.widgets['entries']['rspin']
            rspin.set_digits(numdigits)
            rspin.set_increments(self.stepval, self.stepval*3)

            (decvar, n, s) = info['dec']
            (ravar,  e, w) = info['ra']

            # save variable info for later use by command
            self.arrow_info = Bunch.Bunch(cmd=info['cmd'],
                                          dec_var=decvar, ra_var=ravar)

            # set main units label
            self.widgets['labels']['mainunit'].set_label(info['unit'])
            # set compass label
            txt = compass_template % {'n': n, 's': s, 'e': e, 'w': w }
            self.widgets['labels']['compass'].set_label(txt)

            info = d['button']
            for key in ('cmd', 'dec', 'ra'):
                assert info.has_key(key), \
                       HandsetError("Malformed handset mode: expected key '%s': %s" % (
                    key, str(info)))

            for key in ('dec', 'ra'):
                tup = info[key]
                assert isinstance(tup, list) and (len(tup) == 5), \
                       HandsetError("Malformed handset mode: key '%s': %s" % (
                    key, str(tup)))

            (decvar, decunit, n, s, decval) = info['dec']
            (ravar,  raunit, e, w, raval) = info['ra']

            self.widgets['labels']['lstep'].set_label('%s/%s' % (n, s))
            self.widgets['labels']['rstep'].set_label('%s/%s' % (e, w))
            self.widgets['labels']['lstepunit'].set_label(decunit)
            self.widgets['labels']['rstepunit'].set_label(raunit)
            lspin.set_value(decval)
            rspin.set_value(raval)

            # save variable info for later use by command
            self.button_info = Bunch.Bunch(cmd=info['cmd'],
                                           dec_var=decvar, ra_var=ravar)

        except Exception, e:
            raise e
        
    def load(self, buf):
        d = yaml.load(buf)

        assert isinstance(d, dict) and d.has_key('modes'), \
               HandsetError("Malformed handset def: expected key 'modes': %s" % (
            str(d)))

        self.addModes(d['modes'])

        if d.has_key('tabname'):
            self.setLabel(d['tabname'])

            
    def arrowMove(self, w, axis, mult):
        """Callback when an arrow button is pressed.
        """
        info = self.arrow_info
        stepval = self.widgets['entries']['mainstep'].get_text()
        try:
            stepval = float(stepval)
        except Exception, e:
            common.view.popup_error("Bad step value '%s': %s" % (
                    stepval, str(e)))
            return

        self.logger.debug("Move by arrow: axis=%d mult=%f" % (axis, mult))
        val = stepval * mult
        if axis == 0:
            var = info.dec_var
        else:
            var = info.ra_var
        
        cmdstr = "%s %s=%s" % (info.cmd, var, val)
        self.logger.info("Move by arrow: %s" % (cmdstr))
                         
        try:
            # tag the text so we can manipulate it later
            cmdObj = HandsetCommandObject('hs%d', self.queueName,
                                      self.logger, w, cmdstr)

            common.controller.execOne(cmdObj, 'launcher')
        except Exception, e:
            common.view.popup_error(str(e))


    def execute(self, w):
        """Callback when the 'Move' button is pressed.
        """
        lspin = self.widgets['entries']['lspin']
        rspin = self.widgets['entries']['rspin']

        decoff = lspin.get_value()
        raoff = rspin.get_value()

        info = self.button_info
        cmdstr = "%s %s=%s %s=%s" % (info.cmd, info.dec_var, decoff,
                                     info.ra_var, raoff)
        self.logger.info("Move by button: %s" % (cmdstr))
                         
        try:
            # tag the text so we can manipulate it later
            cmdObj = HandsetCommandObject('hs%d', self.queueName,
                                      self.logger, w, cmdstr)

            common.controller.execOne(cmdObj, 'launcher')
        except Exception, e:
            common.view.popup_error(str(e))


class HandsetCommandObject(CommandObject.CommandObject):

    def __init__(self, format, queueName, logger, widget, cmdstr):
        self.widget = widget
        self.cmdstr = cmdstr

        super(HandsetCommandObject, self).__init__(format, queueName, logger)
        
    def get_preview(self):
        return self.get_cmdstr()
    
    def get_cmdstr(self):
        return self.cmdstr

    def _show_state(self, state):
        if state == 'queued':
            state = 'normal'

        self.widget.modify_bg(gtk.STATE_NORMAL,
                              common.launcher_colors[state])
        
    def mark_status(self, txttag):
        # This MAY be called from a non-gui thread
        common.gui_do(self._show_state, txttag)


##### Icon data #####
    
_icon_left1 = [
"26 26 4 1 0 0",
"       s none  m none  c none",
".      c #00000000D0D0",
"X      c #D0D0D0D0FEFE",
"o      c #00000000FEFE",
"                          ",
"                          ",
"                 .X       ",
"                .oX       ",
"               .X.X       ",
"              .X .X       ",
"             .X  .X       ",
"            .X   .X       ",
"           .X    .X       ",
"          .X     .X       ",
"         .X      .X       ",
"        .X       .X       ",
"       .X        .X       ",
"       .X        .X       ",
"        .X       .X       ",
"         .X      .X       ",
"          .X     .X       ",
"           .X    .X       ",
"            .X   .X       ",
"             .X  .X       ",
"              .X .X       ",
"               .X.X       ",
"                .oX       ",
"                 .X       ",
"                          ",
"                          "]

_icon_left2 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #00000000D0D0",
"X	c #D0D0D0D0FEFE",
"o	c #00000000FEFE",
"                          ",
"                          ",
"               .X   .X    ",
"              .oX  .oX    ",
"             .X.X .X.X    ",
"            .X .X.X .X    ",
"           .X  .oX  .X    ",
"          .X   .X   .X    ",
"         .X   .X    .X    ",
"        .X   .X     .X    ",
"       .X   .X      .X    ",
"      .X   .X       .X    ",
"     .X   .X        .X    ",
"     .X   .X        .X    ",
"      .X   .X       .X    ",
"       .X   .X      .X    ",
"        .X   .X     .X    ",
"         .X   .X    .X    ",
"          .X   .X   .X    ",
"           .X  .oX  .X    ",
"            .X .X.X .X    ",
"             .X.X .X.X    ",
"              .oX  .oX    ",
"               .X   .X    ",
"                          ",
"                          "]

_icon_left3 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #00000000D0D0",
"X	c #D0D0D0D0FEFE",
"o	c #00000000FEFE",
"                          ",
"                          ",
"            .X   .X    .X ",
"           .oX  .oX   .oX ",
"          .X.X .X.X  .X.X ",
"         .X .X.X .X .X .X ",
"        .X  .oX  .X.X  .X ",
"       .X   .X   .oX   .X ",
"      .X   .X    .X    .X ",
"     .X   .X    .X     .X ",
"    .X   .X    .X      .X ",
"   .X   .X    .X       .X ",
"  .X   .X    .X        .X ",
"  .X   .X    .X        .X ",
"   .X   .X    .X       .X ",
"    .X   .X    .X      .X ",
"     .X   .X    .X     .X ",
"      .X   .X    .X    .X ",
"       .X   .X   .oX   .X ",
"        .X  .oX  .X.X  .X ",
"         .X .X.X .X .X .X ",
"          .X.X .X.X  .X.X ",
"           .oX  .oX   .oX ",
"            .X   .X    .X ",
"                          ",
"                          "]

_icon_right1 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"                          ",
"       .X                 ",
"       .oX                ",
"       .X.X               ",
"       .X .X              ",
"       .X  .X             ",
"       .X   .X            ",
"       .X    .X           ",
"       .X     .X          ",
"       .X      .X         ",
"       .X       .X        ",
"       .X        .X       ",
"       .X        .X       ",
"       .X       .X        ",
"       .X      .X         ",
"       .X     .X          ",
"       .X    .X           ",
"       .X   .X            ",
"       .X  .X             ",
"       .X .X              ",
"       .X.X               ",
"       .oX                ",
"       .X                 ",
"                          ",
"                          "]

_icon_right2 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"                          ",
"    .X   .X               ",
"    .oX  .oX              ",
"    .X.X .X.X             ",
"    .X .X.X .X            ",
"    .X  .oX  .X           ",
"    .X   .X   .X          ",
"    .X    .X   .X         ",
"    .X     .X   .X        ",
"    .X      .X   .X       ",
"    .X       .X   .X      ",
"    .X        .X   .X     ",
"    .X        .X   .X     ",
"    .X       .X   .X      ",
"    .X      .X   .X       ",
"    .X     .X   .X        ",
"    .X    .X   .X         ",
"    .X   .X   .X          ",
"    .X  .oX  .X           ",
"    .X .X.X .X            ",
"    .X.X .X.X             ",
"    .oX  .oX              ",
"    .X   .X               ",
"                          ",
"                          "]

_icon_right3 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"                          ",
" .X    .X   .X            ",
" .oX   .oX  .oX           ",
" .X.X  .X.X .X.X          ",
" .X .X .X .X.X .X         ",
" .X  .X.X  .oX  .X        ",
" .X   .oX   .X   .X       ",
" .X    .X    .X   .X      ",
" .X     .X    .X   .X     ",
" .X      .X    .X   .X    ",
" .X       .X    .X   .X   ",
" .X        .X    .X   .X  ",
" .X        .X    .X   .X  ",
" .X       .X    .X   .X   ",
" .X      .X    .X   .X    ",
" .X     .X    .X   .X     ",
" .X    .X    .X   .X      ",
" .X   .oX   .X   .X       ",
" .X  .X.X  .oX  .X        ",
" .X .X .X .X.X .X         ",
" .X.X  .X.X .X.X          ",
" .oX   .oX  .oX           ",
" .X    .X   .X            ",
"                          ",
"                          "]

_icon_up1 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #00000000D0D0",
"X	c #D0D0D0D0FEFE",
"o	c #00000000FEFE",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"            ..            ",
"           .XX.           ",
"          .X  X.          ",
"         .X    X.         ",
"        .X      X.        ",
"       .X        X.       ",
"      .X          X.      ",
"     .X            X.     ",
"    .X              X.    ",
"   .X                X.   ",
"  .o..................o.  ",
"  XXXXXXXXXXXXXXXXXXXXXX  ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          "]

_icon_up2 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #00000000D0D0",
"X	c #D0D0D0D0FEFE",
"o	c #00000000FEFE",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"            ..            ",
"           .XX.           ",
"          .X  X.          ",
"         .X    X.         ",
"        .X      X.        ",
"       .X   ..   X.       ",
"      .X   .XX.   X.      ",
"     .X   .X  X.   X.     ",
"    .X   .X    X.   X.    ",
"   .X   .X      X.   X.   ",
"  .o....X        X....o.  ",
"  XXXXoX          XoXXXX  ",
"     .X            X.     ",
"    .X              X.    ",
"   .X                X.   ",
"  .o..................o.  ",
"  XXXXXXXXXXXXXXXXXXXXXX  ",
"                          ",
"                          ",
"                          ",
"                          "]

_icon_up3 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #00000000D0D0",
"X	c #D0D0D0D0FEFE",
"o	c #00000000FEFE",
"                          ",
"                          ",
"            ..            ",
"           .XX.           ",
"          .X  X.          ",
"         .X    X.         ",
"        .X      X.        ",
"       .X   ..   X.       ",
"      .X   .XX.   X.      ",
"     .X   .X  X.   X.     ",
"    .X   .X    X.   X.    ",
"   .X   .X      X.   X.   ",
"  .o....X        X....o.  ",
"  XXXXoX    ..    XoXXXX  ",
"     .X    .XX.    X.     ",
"    .X    .X  X.    X.    ",
"   .X    .X    X.    X.   ",
"  .o.....X      X.....o.  ",
"  XXXXXoX        XoXXXXX  ",
"      .X          X.      ",
"     .X            X.     ",
"    .X              X.    ",
"   .X                X.   ",
"  .o..................o.  ",
"  XXXXXXXXXXXXXXXXXXXXXX  ",
"                          "]

_icon_down1 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"  ......................  ",
"  XoXXXXXXXXXXXXXXXXXXoX  ",
"   X.                .X   ",
"    X.              .X    ",
"     X.            .X     ",
"      X.          .X      ",
"       X.        .X       ",
"        X.      .X        ",
"         X.    .X         ",
"          X.  .X          ",
"           X..X           ",
"            XX            ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          "]

_icon_down2 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"                          ",
"                          ",
"                          ",
"  ......................  ",
"  XoXXXXXXXXXXXXXXXXXXoX  ",
"   X.                .X   ",
"    X.              .X    ",
"     X.            .X     ",
"  ....o.          .o....  ",
"  XoXXXX.        .XXXXoX  ",
"   X.   X.      .X   .X   ",
"    X.   X.    .X   .X    ",
"     X.   X.  .X   .X     ",
"      X.   X..X   .X      ",
"       X.   XX   .X       ",
"        X.      .X        ",
"         X.    .X         ",
"          X.  .X          ",
"           X..X           ",
"            XX            ",
"                          ",
"                          ",
"                          ",
"                          ",
"                          "]

_icon_down3 = [
"26 26 4 1 0 0",
" 	s none	m none	c none",
".	c #D0D0D0D0FEFE",
"X	c #00000000D0D0",
"o	c #00000000FEFE",
"                          ",
"  ......................  ",
"  XoXXXXXXXXXXXXXXXXXXoX  ",
"   X.                .X   ",
"    X.              .X    ",
"     X.            .X     ",
"      X.          .X      ",
"  .....o.        .o.....  ",
"  XoXXXXX.      .XXXXXoX  ",
"   X.    X.    .X    .X   ",
"    X.    X.  .X    .X    ",
"     X.    X..X    .X     ",
"  ....o.    XX    .o....  ",
"  XoXXXX.        .XXXXoX  ",
"   X.   X.      .X   .X   ",
"    X.   X.    .X   .X    ",
"     X.   X.  .X   .X     ",
"      X.   X..X   .X      ",
"       X.   XX   .X       ",
"        X.      .X        ",
"         X.    .X         ",
"          X.  .X          ",
"           X..X           ",
"            XX            ",
"                          ",
"                          "]

icons = { 'left1': _icon_left1,
          'left2': _icon_left2,
          'left3': _icon_left3,
          'right1': _icon_right1,
          'right2': _icon_right2,
          'right3': _icon_right3,          
          'up1': _icon_up1,
          'up2': _icon_up2,
          'up3': _icon_up3,          
          'down1': _icon_down1,
          'down2': _icon_down2,
          'down3': _icon_down3,          
          }
#END
