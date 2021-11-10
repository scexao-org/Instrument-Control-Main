#
# CommandObject.py -- command object and queue object definitions
#
# Eric Jeschke (eric@naoj.org)
#
import threading

class CommandObject(object):

    # static class vars
    lock = threading.RLock()
    cmdcount = 0

    @classmethod
    def get_tag(cls, format):
        """Class method to bump a count and return unique tags.  _format_
        should be a string containing an integer format instance '%d'.
        """
        with cls.lock:
            tag = format % cls.cmdcount
            cls.cmdcount += 1
            return tag


    def __init__(self, format, queueName, logger):
        """Constructor.  Takes a format string (should contain '%d') and
        a queue name.  Normally this class should be subclassed to provide
        proper behavior for executing a command.
        """
        super(CommandObject, self).__init__()

        self.guitag = CommandObject.get_tag(format)
        self.queueName = queueName
        self.logger = logger
        

    def get_preview(self):
        """This is called to get a preview of the command string that
        should be executed.
        """
        raise Exception("Please subclass this method!")

    def mark_status(self, txttag):
        """This is called when our command changes status.  _txttag_ should
        be queued, unqueued, normal, executing, done, error
        """
        pass

    def __str__(self):
        return self.guitag
        

class SimpleCommandObject(CommandObject):

    def __init__(self, format, queueName, logger, cmdstr):
        self.cmdstr = cmdstr

        super(SimpleCommandObject, self).__init__(format, queueName, logger)
        
    def get_preview(self):
        return self.get_cmdstr()
    
    def get_cmdstr(self):
        return self.cmdstr

    def mark_status(self, txttag):
        pass

class BreakCommandObject(CommandObject):

    def __init__(self, format, queueName, logger, page):
        self.page = page
        
        super(BreakCommandObject, self).__init__(format, queueName, logger)

    def get_preview(self):
        return self.get_cmdstr()
    
    def get_cmdstr(self):
        return '== BREAK =='

    def mark_status(self, txttag):
        pass

class CommentCommandObject(CommandObject):

    def __init__(self, format, queueName, logger, text):
        self.text = text
        
        super(CommentCommandObject, self).__init__(format, queueName, logger)

    def get_preview(self):
        return self.text
    
    def get_cmdstr(self):
        return '== NOP =='

    def mark_status(self, txttag):
        pass

