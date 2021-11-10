
class SOSSfifoError(Exception):
    pass

class SOSSfifoMsgError(SOSSfifoError):
    pass

class SOSSfifoMsg(object):
    """Abstract base class for specific SOSS FIFO messages.
    """

    def __init__(self):
        self.kind = ''
        self.reserved = ''

        # Offical FIFO message size
        self.msg_len = 100


    def set(self, **kwdargs):
        """Convenience function for setting message values.  Set arbitrary
        instance variables from keyword arguments provided by the caller.
        """
        self.__dict__.update(kwdargs)


    def msgCheck(self, msgstr):
        length = len(msgstr)
        if length != self.msg_len:
            raise SOSSfifoMsgError("Message size (%d) is not correct (=%d)" %
                                   (length, self.msg_len))

    def padNull(self, msgstr, size):
        length = len(msgstr)
        if length >= size:
            return msgstr
        return msgstr + ''.join(['\00' for i in xrange(size - length)])

        
    def message2str(self):
        
        msgstr = "%8.8s%92.92s" % (
            self.kind,
            self.reserved )

        self.msgCheck(msgstr)

        return msgstr
                                  

    def __str__(self):
        return self.message2str()


#END SOSSfifo.py

