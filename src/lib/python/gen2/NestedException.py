# An exception class that can be nested.
# The motivation here is to retain the stack trace
# information all the way down to where the
# root exception occured.
#
# Yasuhiko Sakakibara <yasu@subaru.naoj.org> 
import traceback

class NestedException(Exception):
    def __init__(self, exception, message = ""):
        Exception.__init__(self, message)
        self.exception = exception
        self.traceBack = traceback.format_stack()[:-2]
            
    
    def __str__(self):
        mes = ''
        if self.exception:
            mes = str(self.exception)
        return "%s : %s\n%s" % (self.__class__.__name__,
                                Exception.__str__(self), 
                                str(self.exception))
                                
    def formatStackTrace(self):
        result = self.__class__.__name__ + "\n"
        result = result + "".join(self.traceBack) + "\n"
        if self.exception and isinstance(self.exception, NestedException):
            result = result + self.exception.formatStackTrace()
        return result
    