#! /usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jan 12 13:07:30 HST 2012
#]

import sys, time
import alsaaudio, wave
import cStringIO
import threading
#import numpy

class SoundRecorder(object):

    def __init__(self, card='default', compress=False):
        self.card = card
        self.samples = []

    def _setup(self):
        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL,
                            self.card)
        inp.setchannels(1)
        inp.setrate(44100)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        inp.setperiodsize(1024)
        #inp.setperiodsize(160)
        self.inp = inp


    def recordToWAV(self, out_f, ev_quit):
        self._setup()
        
        w = wave.open(out_f, 'w')
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)

        while not ev_quit.isSet():
            l, data = self.inp.read()
            ## a = numpy.fromstring(data, dtype='int16')
            ## print numpy.abs(a).mean()
            w.writeframes(data)
            time.sleep(0)
        w.close()

    def recordToWAVbuffer(self, ev_quit):
        out_f = cStringIO.StringIO()
        self.recordToWAV(out_f, ev_quit)
        buf = out_f.getvalue()
        out_f.close()
        return buf

    def recordToWAVbufferSave(self, ev_quit):
        buf = self.recordToWAVbuffer(ev_quit)
        self.samples.append(buf)

    def getSavedSample(self):
        return self.samples.pop(0)

    def recordToWAVfile(self, outfile, ev_quit):
        out_f = open(outfile, 'w')
        self.recordToWAV(out_f, ev_quit)
        out_f.close()


def main(options, args):
    
    if options.showcards:
        for card in alsaaudio.cards():
            print card
        sys.exit(0)

    obj = SoundRecorder(options.card)
        
    if options.record:
        outfile = options.record
        if not '.' in outfile:
            outfile = '%s.wav' % outfile

        ev_quit = threading.Event()
        print "Press ENTER to stop recording..."
        t = threading.Thread(target=obj.recordToWAVfile, args=(outfile, ev_quit))
        t.start()
        sys.stdin.readline()
        ev_quit.set()
        t.join()


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--card", dest="card", default='default',
                      help="Specify audio card to use for recording")
    optprs.add_option("--showcards", dest="showcards", default=False,
                      action="store_true",
                      help="Show the available audio cards")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-r", "--record", dest="record", 
                      help="Record a WAV file")
    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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
