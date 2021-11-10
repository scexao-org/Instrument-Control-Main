#!/usr/bin/env python

import sys
import os

# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QVariant', 2)

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog


progname = os.path.basename(sys.argv[0])
    
# class ImgRot(QtGui.QLabel): ''' state of the telescope in
#     pointing/slewing/tracking/guiding ''' def __init__(self,
#     parent=None, width=125, height=20, logger=None): super(ImgRot,
#     self).__init__(parent)

#         self.bg='white'
#         self.alarm='red'
#         self.normal='green'
#         self.warn='orange'
#         self.w=width
#         self.h=height

#         self.img_out='ImgRot Out'
#         self.img_free='ImgRot Free'
#         self.img_link='ImgRot Link'
#         self.img_zenith='ImgRot Zenith'
#         self.img_undef='ImgRot Undefined'
#         self.logger=logger
       
#         self.__init_label()

#     def __init_label(self):
#         self.font = QtGui.QFont('UnDotum', 11.5) 
#         self.setText('Initializing')
#         self.setAlignment(QtCore.Qt.AlignCenter)
#         self.setFont(self.font)

#         self.setStyleSheet("QLabel {color :%s ; background-color:%s}" %(self.normal, self.bg))

#     def minimumSizeHint(self):
#         return QtCore.QSize(self.w, self.h)

#     def sizeHint(self):
#         return QtCore.QSize(self.w, self.h)


class ImgRot(Canvas): 
    ''' image rotatro  ''' 
    def __init__(self, parent=None, logger=None):
        super(ImgRot, self).__init__(parent=parent, fs=11.5, width=125, height=40, logger=logger )

        self.img_out='ImgRot Out'
        self.img_free='ImgRot Free'
        self.img_link='ImgRot Link'
        self.img_zenith='ImgRot Zenith'
        self.img_undef='ImgRot Undefined'

 
    def update_imgrot(self, imgrot, mode, focus):
        ''' imgrot=TSCV.ImgRotRotation
            mode=TSCV.ImgRotMode
            focus=TSCV.FOCUSINFO
        ''' 

        imgout=[0x10000000, 0x20000000,  0x00040000,  
                0x00100000, 0x00200000,  0x00000400, 
                0x00002000, 0x00004000,  0x00000008, 0x00000000]

        color=self.normal

        if focus in imgout:
            text=self.img_out
        elif imgrot == 0x02 or mode == 0x02:
            text = self.img_free
            color=self.warn
        elif imgrot == 0x01 and mode == 0x01:
            text = self.img_link
        elif imgrot == 0x01 and mode == 0x40:
            text = self.img_zenith
        else:
            text=self.img_undef
            color=self.alarm
        return (text, color)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        rindx=random.randrange(0, 7)
        mindx=random.randrange(0, 8)
        findx=random.randrange(0, 34)
        iindx=random.randrange(0, 6)

        imgrot=[0x01, None, '##STATNONE##',  0x02, '##NODATA##', '##ERROR##']
        mode=[0x01,  None, '##STATNONE##', 0x40, '##NODATA##', 0x02, '##ERROR##']

        foci=[0x01000000, 0x11111111, 0x02000000, 0x00001000, 0x04000000,
              0x08000000, 0x10000000, 0x20000000, 0x40000000, 0x80000000L, 
              0x00010000, 0x00020000, 0x00100000, 0x00200000, 0x00400000, 
              0x00800000, 0x00000100, 0x00000200, 0x00002000, 0x00004000,
              0x00008000, 0x00000001, 0x00000002, 0x00000004, 0x00040000,
              0x00080000, 0x00000400, 0x00000800, 0x00000800, 0x00000008, 
              0x00000010, 0x00000000]

        itype=[0x12, 0x10, 0x0C, 0x04, 0x14, None]

        try:
            imgrot=imgrot[rindx]
            mode=mode[mindx]
            focus=foci[findx]
            itype=itype[iindx]
        except Exception as e:
            imgrot=0x01
            mode=0x01
            focus=0x00000010
            itype=0x12
            print e
        
        self.update_imgrot(imgrot, mode, focus, itype)


class ImgRotNsOpt(ImgRot):
    '''  Nasmyth Optical image rotator  '''
    def __init__(self, parent=None, logger=None):
        super(ImgRotNsOpt, self).__init__(parent=parent, logger=logger)

    def update_imgrot(self, imgrot, mode, focus, itype):
        
        self.logger.debug('rot=%s mode=%s  focus=%s itype=%s' %(str(imgrot), str(mode), str(focus), str(itype)))

        # img-rot blue
        imrb=[0x40000000, 0x80000000L, 0x00400000, 0x00800000, 0x00008000, 0x00000001]
        # img-rot red
        imrr=[0x00010000, 0x00020000,  0x00000100, 0x00000200, 0x00000002, 0x00000004]         

        # image-rot type
        itypes={0x12:imrb, 0x10:'(OnWay-Blue)', 0x0C:imrr, 0x04:'(OnWay-Red)', 0x14:'(none type)'}

        text, color=ImgRot.update_imgrot(self, imgrot, mode, focus)

        if text in [self.img_free, self.img_link, self.img_zenith]:          

            try:    
                res=itypes[itype]
                self.logger.debug('res=%s' %res)
                if type(res)==list:
                    if focus in imrb:
                        text+='\n(Blue)'
                    elif focus in imrr:
                        text+='\n(Red)'
                    else:
                        text+='\n(type undef)'
                        color=self.warn
                else:
                    text+='\n'+res
            except KeyError:
                text+='\n(type undef)'
                color=self.warn 


            # if itype ==0x12:
            #     if focus in imrb:
            #         text+='\n(Blue)' 
            #     else:
            #         text+='\n(Blue?)'
            #         color=self.warn
            # elif itype ==0x10:
            #     text+='\n(OnWay-Blue)'
            # elif itype ==0x0C:
            #     if focus in imrr: 
            #         text+='\n(Red)'
            #     else:
            #         text+='\n(Red?)'
            #         color=self.warn
            # elif itype ==0x04:
            #     text+='\n(OnWay-Red)'
            # elif itype ==0x14:
            #     text+='\n(none type)'
            # else:
            #     text+='\n(type undef)'
            #     color=self.warn 

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" %(color, self.bg))


class ImgRotNsIr(ImgRot):
    ''' state of the telescope in pointing/slewing/tracking/guiding  '''
    def __init__(self, parent=None, logger=None):
        super(ImgRotNsIr, self).__init__(parent=parent, logger=logger)

    def update_imgrot(self, imgrot, mode, focus, itype=None):
     
        self.logger.debug('rot=%s mode=%s  focus=%s ' %(str(imgrot), str(mode), str(focus), ))

        aoin= 0x00000000
        text, color=ImgRot.update_imgrot(self, imgrot, mode, focus)

        if text==self.img_out:
            if focus==aoin:
                self.logger.debug('focus ao=%s' %str(focus))
                text+='\n(AO In)'
            else:
                text+='\n(AO Out)'  
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" %(color, self.bg))


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('insrot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=125; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)

            if options.mode=='nsir':
                ins = ImgRotNsIr(parent=self.main_widget, logger=logger)
            elif options.mode=='nsopt':
                ins = ImgRotNsOpt(parent=self.main_widget, logger=logger)
            l.addWidget(ins)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), ins.tick)
            timer.start(options.interval)

            self.main_widget.setFocus()
            self.setCentralWidget(self.main_widget) 
            self.statusBar().showMessage("%s starting..." %options.mode, options.interval)

        def closeEvent(self, ce):
            self.close()

    try:
        qApp = QtGui.QApplication(sys.argv)
        aw = AppWindow()
        print 'state'
        #state = State(logger=logger)  
        aw.setWindowTitle("%s" % progname)
        aw.show()
        #state.show()
        print 'show'
        sys.exit(qApp.exec_())

    except KeyboardInterrupt, e:
        logger.warn('keyboard interruption....')
        sys.exit(0)



if __name__ == '__main__':
    # Create the base frame for the widgets

    from optparse import OptionParser
 
    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--interval", dest="interval", type='int',
                      default=1000,
                      help="Inverval for plotting(milli sec).")
    # note: there are sv/pir plotting, but mode ag uses the same code.  
    optprs.add_option("--mode", dest="mode",
                      default='ag',
                      help="Specify a plotting mode [nsir |nsopt]")

    ssdlog.addlogopts(optprs)
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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

