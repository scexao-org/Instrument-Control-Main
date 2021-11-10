#
# SkycatControl.py -- support class for controlling the Skycat FITS display
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Jul 18 10:11:57 HST 2011
#]
#
import socket
import time

class SkycatError(Exception):
    pass

class SkycatControl(object):
    """Provides a class that can control the Skycat application through its
    remote control socket interface.
    """

    def __init__(self, host, port, logger):
        self.host = host
        self.port = port
        self.logger = logger
        self.instance = ".skycat1"
        self.imagepath = "%s.image" % (self.instance)

    def close(self):
        try:
            self.sock.close()
        except:
            pass
        
    def connect(self):
        self.close()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.connect((self.host, self.port))

        except Exception, e:
            raise SkycatError("Cannot connect to skycat RTD: %s" % (
                str(e)))

    def send_command(self, cmdstr):
        try:
            self.logger.debug("Sending: '%s'" % (cmdstr))
            self.sock.send(cmdstr + '\n')

        except Exception, e:
            raise SkycatError("Cannot communicate to skycat RTD: %s" % (
                str(e)))

        try:
            buf = self.sock.recv(50000)
            print buf
            i = buf.index('\n')
            line = buf[:i]
            status, length = map(int, line.split())
            result = buf[i+1:]
            i = 0
            while (len(result) < length) and (i < 10):
                n = length - len(result)
                time.sleep(0.01)
                result = result + self.sock.recv(n)
            
        except Exception, e:
            raise SkycatError("Error parsing acknowledgement from skycat RTD: %s" % (
                str(e)))
        
        if status != 0:
            raise SkycatError("Error acknowledgement from skycat RTD: (%s) %s, %s" % (
                status, length, cmdstr))

        self.logger.debug("Result: '%s'" % (result))
        return result

# From the skycat source code:
# usage: $image mmap set $data_filename $data_offset $data_owner \
#                       ?$header_filename $header_offset $header_owner?
#        $image mmap get data
#        $image mmap get header
#        $image mmap create $filename $size
#        $image mmap delete $filename
#        $image mmap update

    def update_image(self):
        # From the skycat source code:
        # $image mmap update
        # "The "update" command causes the display to be updated to reflect any
        #  changes in the image memory."
        self.send_command('mmap update')

    def send_tcl(self, tclsrc):
        return self.send_command('remotetcl "%s"' % tclsrc)

    def update_object(self, objname):
        obj_path = "%s.panel.info.object.entry" % (self.imagepath)
        self.send_tcl('%s delete 0 100; %s insert 0 %s' % (
            obj_path, obj_path, objname))

    def update_title(self, title):
        title = title.replace(' ', '-')
        self.send_tcl('wm title %s %s' % (self.instance, title))
        

#END
