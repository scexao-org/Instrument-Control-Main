#!/usr/bin/env python

import sys
import os
import ssdlog


from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

progname = os.path.basename(sys.argv[0])
    

class State(Canvas):
    ''' state of the telescope in pointing/slewing/tracking/guiding  '''
    def __init__(self, parent=None, logger=None ):

        self.fg='white'
        self.bg='green'
        super(State, self).__init__(parent=parent, fs=27, width=350, \
                                    height=75, fg='white', \
                                    bg='green', logger=logger )

    def update_state(self, state, intensity, valerr, calc_mode=None):
        ''' state=STATL.TELDRIVE, 
            intensity=TSCL.AG1Intensity | TSCL.SV1Intensity 
                      TSCL.AGPIRIntensity | TSCL.AGFMOSIntensity
                      TSCL.HSC.SCAG.Intensity | TSCL.HSC.SHAG.Intensity
            valerr = STATL.AGRERR | STATL.SVRERR 
            calc_mode = STATL.SV_CALC_MODE '''

        self.logger.debug('state=%s, intensity=%s valerr=%s calc_mode=%s' %(state, intensity, valerr, calc_mode))

        guiding = ("Guiding(AG1)", "Guiding(AG2)", \
                   "Guiding(SV1)","Guiding(SV2)", \
                   "Guiding(AGPIR)", "Guiding(AGFMOS)", \
                   "Guiding(HSCSCAG)", "Guiding(HSCSHAG)")       
        slewing = 'Slewing'
        sv_guiding = ("Guiding(SV1)", "Guiding(SV2)")

        bg = self.normal
        if state in ERROR:
            self.logger.debug('state=%s in error' %(state))   
            state = "Unknown" 
            bg = self.alarm
        elif state == slewing:
            bg = self.warn
        elif state in guiding:
            if intensity in ERROR or valerr in ERROR:
                bg = self.alarm 
            elif intensity < 1.0:
                bg = self.alarm
            elif valerr >= 1000.0:
                bg = self.alarm
            elif valerr >= 500.0:
                bg = self.warn
            
            # if sv guiding, add calculation mode to state 
            if state in sv_guiding:
                state = '%s(%s)' %(state, calc_mode)
                self.logger.debug('sv state=%s' %(state))
        # else is pointing, tracking with green color

        self.logger.debug('state=%s bg=%s' %(state, bg))
        self.setStyleSheet("QLabel {color :%s; background-color:%s}" %(self.fg, bg) )
        self.setText(state)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        num_state = random.randrange(0,15)
        num_intensity = random.randrange(0,4)
        num_valerr = random.randrange(0,5)        

        state = ["Guiding(AG1)", "Guiding(AG2)", "Unknown", "##NODATA##",
               "##ERROR##", "Guiding(SV1)","Guiding(SV2)", "Guiding(AGPIR)",
               "Guiding(AGFMOS)", "Tracking", "Tracking(Non-Sidereal)", 
               "Slewing", "Pointing", "Guiding(HSCSCAG)", "Guiding(HSCSHAG)"]
      
        intensity = [-1, 1 ,"##NODATA##", 1,  "##ERROR##"]
        valerr = [1000.0, 0, 500.0, "##NODATA##", 100.0, "##ERROR##"]
        calc_mode = ['CTR', 'SLIT', 'PK', 'BSECT', "##NODATA##"]
        try:
            state = state[num_state]
            intensity = intensity[num_intensity]
            valerr = valerr[num_valerr]
            calc_mode = calc_mode[num_valerr]
            self.logger.debug('state=%s, intensity=%s valerr=%s calc_mode=%s' %(state, intensity, valerr, calc_mode)) 
            self.update_state( state, intensity, valerr, calc_mode)
        except Exception as e:
            pass

# class NsOptState(State):
#     ''' nsopt state of the telescope in pointing/slewing/tracking/guiding  '''
#     def __init__(self, parent=None, logger=None ):
#         super(NsOptState, self).__init__(parent=parent, logger=logger )

#     def update_state(self, state, ag_intensity, ag_valerr, sv_intensity, sv_valerr):
#         ''' state=STATL.TELDRIVE, 
#             ag/sv_intensity=TSCL.AG1Intensity/TSCL.SV1Intensity 
#             ag/sv_valerr = STATL.AGRERR/STATL.SVRERR '''


# #        self.logger.debug('state=%s, intensity=%s valerr=%s' %(state, intensity, valerr))

#         ag_guiding=("Guiding(AG)", "Guiding(AG1)", "Guiding(AG2)")
#         sv_guiding=("Guiding(SV)", "Guiding(SV1)", "Guiding(SV2)")

#         if state in sv_guiding:
#             intensity, valerr = sv_intensity, sv_valerr
#         elif state in ag_guiding:
#             intensity, valerr = ag_intensity, ag_valerr 
#         # if state is not guiding, the values of intensity and valerr do not matter. 
#         State.update_state(self, state, intensity=0, valerr=0)

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=350; self.h=75;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            
            state = State(parent=self.main_widget, logger=logger)
            l.addWidget(state)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), state.tick)
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
                      help="Specify a plotting mode [ag|nsopt|fmos]")

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

