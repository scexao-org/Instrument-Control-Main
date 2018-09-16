#!/usr/bin/env python
import serial
import os
import time
import binascii
import time

home = os.getenv('HOME')
sdir = home+'/conf/scexao_status/' # status directory

brate = 9600 # baud rate for EZ-stepper circuits
tout  = 0.2  # time out for serial connection (in sec)
delay = 0.1  # safety delay between send - receive

mxstp = 18000000 # max nbr of steps (for home command only)

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")

# ---------------------------------------------------
#      utility to signal the status monitor
# ---------------------------------------------------

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

# --------------------------------------------------------
#  utility to translate the reply from the stepper circuit
# --------------------------------------------------------

def ezs_response(cmd, data, quiet=False):
    res = ""
    a = binascii.b2a_hex(data)

    if not quiet:
        print "cmd      = ", cmd
        print "reply    = ", a

    if cmd[2] == "?" and a != '':
        b   = (a.split('ff2f30'))[1]
        c   = (b.split('030d0a'))[0]
        res = binascii.a2b_hex(c[2:])
    return res

# -------------------------------------------
#  this is EZ stepper chain class definition
# -------------------------------------------

class ezstep_chain:
    def __init__(self, dev="/dev/null"):
        if dev != "/dev/null":
            if os.path.islink(dev):
                dummy = os.path.split(dev)
                self.id = dummy[1]
                ddir = dummy[0]
                link = os.readlink(dev)
                self.dev = os.path.join(ddir, link)
            else:
                self.dev = dev
                self.id  = os.path.split(dev)[1]
            try:
                self.ser = serial.Serial(self.dev, brate, timeout=tout)
            except:
                self.ser = None
                print("Device %s either not connected or not powered" % \
                          (self.dev,))
                return(None)

            temp = self.ser.readlines() # flush the port

            self.ser.write('/1&R\r\n')
            time.sleep(delay)
            msg = self.ser.readline()
            
            if "EZStepper" in msg:
                self.idns = []
                cnt = 0
                tmp = ""
                for i in xrange(9):
                    self.ser.write('/%d&R\r\n' % (i+1,))
                    time.sleep(delay)
                    msg = self.ser.readline()
                    if msg != "":
                        cnt += 1
                        tmp += "-%d-" % (i+1,)
                        self.idns.append(i+1)
                self.ns = cnt
                print("This chain contains %d EZ stepper circuits (ID: %s)" % \
                          (self.ns, tmp))
            else:
                print("Device %s is not recognized as a EZ stepper chain" % \
                          (self.dev,))
                print("The chain may simply not be powered up.")
                self.ser.close()
                return(None)

            # create current file if it doesn't exist yet
            current = sdir + self.id + '.txt'  # config file
            if not os.path.exists(current):
                f = open(current, 'w')
                for i in xrange(self.ns):
                    f.write("%d 0\n" % (self.idns[i],))
                f.close()

            # either way, signal the status monitor
            touch(sdir+'updt')
        else:
            self.id = "null"
            self.dev = dev

    def current_pos(self, idn):
        ''' --------------------------------------------------------
        Simply returns the current position known by the circuit
        -------------------------------------------------------- '''
        cmd = "/%d?R" % (idn,)
        pos = self.command(cmd, quiet=True)
        try:
            res = int(pos)
        except:
            res = None
        return(res)

    def is_congruent(self, idn):
        ''' --------------------------------------------------------
        Check that the EZ-stepper circuit status is congruent with 
        what is stored in the file written to disk.
        -------------------------------------------------------- '''

        res = False                        # default assumption
        current = sdir + self.id + '.txt'  # config file

        if os.path.exists(current):
            lines = open(current, 'r+').readlines()
            nl = lines.__len__() # number of lines

            for i in range(nl):
                data = lines[i].split()
                if int(data[0]) == int(idn): # found the matching line
                    # query the circuit
                    pos = self.current_pos(idn)
                    if int(data[1]) == int(pos):
                        res = True
        return(res)

    def home(self, idn):
        cmd = "/%dZ%dR" % (idn, mxstp,)
        self.ser.write(cmd+'\r\n')
        current = sdir + self.id + '.txt'
        self.updt_current(idn, 0)

    def goto(self, idn, dest=0):
        ''' --------------------------------------------------------
        Move to an absolute position "dest" in steps.
        -------------------------------------------------------- '''
        if not self.is_congruent(int(idn)):
            print("Circuit status not congruent. Home or reset?")
            return(None)
        else:
            if 0 <= dest < mxstp:
                res = self.command("/%dA%dR" % (idn,dest,), quiet=True)
                # wait until we get there?
                pos = dest
                self.updt_current(idn, pos)
                return(True)
            else:
                print("Required position cannot be reached.")
                return(False)

    def dmove(self, idn, delta):
        ''' --------------------------------------------------------
        Relative mobe by a "delta" in steps.
        The use of this function is for now reserved for the
        tip-tilt stages only.
        -------------------------------------------------------- '''
        print("delta = %s" % (delta,))

        if abs(int(delta)) == 0:
            print("forbidden: move by zero")
            return(False)
        elif abs(int(delta)) > 1000:
            print("forbidden: move too large")
            return(False)
        else:
            print("Good, the force is strong with you")
            if delta > 0: cmd = "P"
            else:         cmd = "D"
            res = self.command("/%d%s%dR" % (idn, cmd, abs(delta)), quiet=False)
            #print ("/%d%s%dR" % (idn, cmd, abs(delta)))
            return(True)

    def sg1_move(self, idn, delta):
        ''' --------------------------------------------------------
        Relative move by a "delta" in steps.
        The use of this function is for now reserved for the
        stargate. It is essentially the same as dmove, but
        without the restriction on large moves.
        -------------------------------------------------------- '''
        print("delta = %s" % (delta,))

        if abs(int(delta)) == 0:
            print("forbidden: move by zero")
            return(False)
        else:
            print("Symbols are selected. The stargate is moving")
            if delta > 0: cmd = "P"
            else:         cmd = "D"
            res = self.command("/%d%s%dR" % (idn, cmd, abs(delta)), quiet=False)
            return(True)

    def updt_current(self, idn, pos):
        ''' --------------------------------------------------------
        Refreshes the current position file accordingly with
        circuit status.
        -------------------------------------------------------- '''
        current = sdir + self.id + '.txt'
        lines = open(current, 'r+').readlines()
        for i in xrange(lines.__len__()):
            data = lines[i].split()
            if int(data[0]) == int(idn):
                lines[i] = data[0] + ' ' + str(pos) + '\n'
        open(current, 'w').writelines(lines)
        touch(sdir+'updt')


    def reset(self, idn):
        ''' --------------------------------------------------------
        Reset is the term chosen to re-set the EZ-stepper circuit
        to the last saved position without moving anythin on the
        actual system.
        -------------------------------------------------------- '''
        current = sdir + self.id + '.txt'
        lines = open(current, 'r').readlines()
        ns = lines.__len__()

        # only two stepper chains in the system
        #if ns > 4: self.init_linear()
        #else:      self.init_tts()
        self.init_combined()

        for i in xrange(ns):
            data = lines[i].split()
            if int(data[0]) == int(idn):
                pos = int(data[1])
                print('/%dz%dR' % (idn, pos,))
                self.command('/%dz%dR' % (idn, pos,), quiet=False)
                return(True)

    def command(self, cmd, quiet=False):
        ''' --------------------------------------------------------
        Command is a low level access to the stepper, that does not 
        include any safeguard. The function should only be used from
        within the ezstep_chain class, or else, by someone who
        understands that he can drive the stage beyond its limit and
        potentially break something.
        -------------------------------------------------------- '''
        self.ser.write(cmd+'\r\n')
        time.sleep(delay)
        dummy = self.ser.readline()
        resp = ezs_response(cmd, dummy, quiet=quiet)
        if not quiet:
            print(resp)
        return(resp)

    def init_combined(self, quiet=False):

        ''' ------------------------------------------------------
        This is the sequence to set the stepper circuit parameters
        right so that the Newport tip-tilt stages actually move.
        ------------------------------------------------------ '''
        self.command("/1m100L100h10V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/2m100L100h10V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/3m100L100h10V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/4m100L100h10V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/1z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/1z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/2z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/2z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/3z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/3z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/4z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/4z1000000R", quiet=quiet)
        time.sleep(delay)

        ''' ------------------------------------------------------
        This is the sequence to set the stepper circuit parameters
        right so that the linear translation stages move properly.
        ------------------------------------------------------ '''
        # camera stage
        self.command("/5F1j256V500000L500m50h05R", quiet=quiet)
        time.sleep(delay)

        # vampire's polarizer
        self.command("/7F1V900000m25h05R", quiet=quiet)
        time.sleep(delay)

        # inverse piaa stage
        self.command("/8F1j256V900000m25h05R", quiet=quiet)
        time.sleep(delay)

    def init_smi (self, quiet=False):
        ''' ------------------------------------------------------
        This is the sequence to set the stepper circuit parameters
        for the single mode injection cariage device
        ------------------------------------------------------ '''
        self.command("/3F1j256V500000L500m50h05R", quiet=quiet)
        time.sleep(delay)

    def init_tts(self, quiet=False):
        ''' ------------------------------------------------------
        This is the sequence to set the stepper circuit parameters
        right so that the Newport tip-tilt stages actually move.
        ------------------------------------------------------ '''
        self.command("/1m100L100h30V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/2m100L100h30V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/3m100L100h30V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/4m100L100h30V30000P100D100R", quiet=quiet)
        time.sleep(delay)
        self.command("/1z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/1z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/2z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/2z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/3z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/3z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/4z1000000R", quiet=quiet)
        time.sleep(delay)
        self.command("/4z1000000R", quiet=quiet)
        time.sleep(delay)


    def init_linear(self, quiet=False):
        ''' ------------------------------------------------------
        This is the sequence to set the stepper circuit parameters
        right so that the linear translation stages move properly.
        ------------------------------------------------------ '''
        # camera stage
        self.command("/5F1j256V500000L500m60h05R", quiet=quiet)
        time.sleep(delay)

        # dichroic linear stage
        self.command("/6F1j256V500000L500m60h05R", quiet=quiet)
        time.sleep(delay)

        # vampire's polarizer
        self.command("/7F1V900000m25h05R", quiet=quiet)
        time.sleep(delay)

        # inverse piaa stage
        self.command("/8F1V900000m25h05R", quiet=quiet)
        time.sleep(delay)

    def close(self):
        if self.ser != None:
            self.ser.close()
