# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Oct 22 15:08:05 HST 2010
#]

import os
import gtk

import myproc

import common
import CodePage, OpePage


class InfPage(CodePage.CodePage):

    def __init__(self, frame, name, title):

        super(InfPage, self).__init__(frame, name, title)

        # add some bottom buttons
        self.btn_makeope = gtk.Button("Make OPE")
        self.btn_makeope.connect("clicked", lambda w: self.makeope('app2ope.pl -'))
        self.btn_makeope.show()
        self.leftbtns.pack_end(self.btn_makeope)

        self.btn_makedarks = gtk.Button("Make Darks")
        self.btn_makedarks.connect("clicked", lambda w: self.makeope('mkDARKope.pl -'))
        self.btn_makedarks.show()
        self.leftbtns.pack_end(self.btn_makedarks)

    def makeope(self, cmdstr):
        # get text to process
        start, end = self.buf.get_bounds()
        buf = self.buf.get_text(start, end)

        try:
            proc = myproc.myproc(cmdstr)
            # write input to stdin
            proc.stdin.write(buf)
            proc.stdin.close()

            # This will force a reap
            proc.status()
            output = proc.output()
            #print output

            # make ope file path
            infdir, inffile = os.path.split(self.filepath)
            infpfx, infext = os.path.splitext(inffile)

            opepath = os.path.join(infdir, '%s.ope' % infpfx)

            common.view.open_generic(common.view.exws, output, opepath,
                                     OpePage.OpePage)

        except Exception, e:
            return common.view.popup_error("Cannot generate ope file: %s" % (
                    str(e)))


#END
