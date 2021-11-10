#
# CommandParser -- routines for tokenizing and parsing SOSS-style commands
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 24 12:23:40 HST 2007
#]

def _convertToken(strToken):
    """Generic token->value converter.  Tries to convert token to a number
    and, failing that, leaves it as a string.
    
    See use in convertArg() method of CommandParser.
    """
    try:
        return int(strToken)
    except ValueError:
        pass
    try:
        return float(strToken)
    except ValueError:
        pass
    return strToken


class CommandParserError(Exception):
    pass


class CommandParser(object):
    """This class provides methods for tokenizing and parsing SOSS-style
    commands; e.g.
       EXEC SUBSYS COMMAND PARAM1=VAL1 PARAM2=VAL2 ...
    """

    def __init__(self):
        self.whitespace = (' ', '\t', '\n')
        self.quotes = ('"', "'")
        self.terminators = (';')

        self.start_quote = None
        self.chars = []             # Character buffer
        self.tokens = []            # Token buffer


    def _make_token(self):
        # Make a token by concatenating all characters in the char buffer.
        token = ''.join(self.chars)
        self.tokens.append(token)
        # Clear char buffer
        self.chars = []
            

    def tokenize(self, cmdstr):
        """Tokenizes a command string by lexing it into tokens.
        """

        charlst = list(cmdstr)
        self.tokens = []
        self.start_quote = None
        self.chars = []

        while len(charlst) > 0:
            c = charlst.pop(0)

            # process double quotes
            if c in self.quotes:
                # if we are not building a quoted string, then turn on quote
                # flag and continue scanning
                if not self.start_quote:
                    self.start_quote = c
                    continue
                elif self.start_quote != c:
                    self.chars.append(c)
                    continue
                else:
                    # end of quoted string; make token
                    self._make_token()
                    self.start_quote = None
                    continue

            # process white space
            elif c in self.whitespace:
                if self.start_quote:
                    self.chars.append(c)
                    continue
                else:
                    if len(self.chars) > 0:
                        self._make_token()
                    continue

            # process white space
            elif c in self.terminators:
                if self.start_quote:
                    self.chars.append(c)
                    continue
                else:
                    # Terminate existing token
                    if len(self.chars) > 0:
                        self._make_token()
                    # Make token from terminator
                    self.chars = [c]
                    self._make_token()
                    continue
                    
            # "normal" char
            else:
                self.chars.append(c)
                continue

        if len(self.chars) > 0:
            self._make_token()

        if self.start_quote:
            raise CommandParserError("Unterminated quotation: '%s'" % cmdstr)

        return self.tokens


    def convertArg(self, valueStr, paramType):
        """Converts a _valueStr_ into a value depending on _paramType_.
        _paramType_ should be one of: ('NUMBER', 'CHAR')
        """

        # If _paramType_ is a callable, then it is a specific conversion
        # function
        if callable(paramType):
            return paramType(valueStr)

        # What are all possible types?
        paramType = paramType.upper()
        try:
            if paramType == 'INT':
                return int(valueStr)
            elif paramType == 'FLOAT':
                return float(valueStr)
            elif paramType == 'NUMBER':
                try:
                    return int(valueStr)
                except ValueError:
                    return float(valueStr)
            elif paramType == 'CHAR':
                return valueStr
            else:
                # Default to string for all others??
                return valueStr
        except ValueError:
            raise CommandParserError("Error converting parameter '%s' to number" % \
                                             valueStr)


    def parseParams(self, tokenList, paramTypes="guess", lowercase=True):
        """Parse a tokenList into a list of arguments and a dictionary of
        keyword arguments.  If _lowercase_ is True then keyword arguments
        will have the keys lowercased.  If _paramTypes_ is passed in,
        then it specifies types for the keyword arguments for the purpose
        of converting the values.
        """
        args = []
        kwdargs = {}
        
        for token in tokenList:
            # TODO: this should really be fixed to take into account quotation;
            # i.e.  PARAM1="ARG=FOO" needs to NOT split on the embedded "="
            if '=' in token:
                # keyword argument
                try:
                    (var, val) = token.strip().split('=')
                except (ValueError, IndexError):
                    raise CommandParserError("Malformed command parameter '%s'" % token)
                        
                ucvar = var.upper()
                if lowercase:
                    var = var.lower()

                # Convert parameter from a string to a value if we have a
                # mapping for it in paramTypes
                if paramTypes == "guess":
                    # Best guess conversion
                    val = self.convertArg(val, _convertToken)
                    
                elif (type(paramTypes) == dict) and \
                         (paramTypes.has_key(ucvar)):
                    # Explicit one-on-one mappings provided via a dict
                    val = self.convertArg(val, paramTypes[ucvar])

                else:
                    val = self.convertArg(val, paramTypes)
                    
                kwdargs[var] = val
                continue

            # not keyword arg; just append to args list
            args.append(token)

        return (args, kwdargs)
    
            
    def parseLines(self, tokenList):
        """Split a long list of tokens into a list of lists, where each
        sublist contains no line terminators.
        """
        lines = []
        line = []
        for token in tokenList:
            if token in self.terminators:
                lines.append(line)
                line = []
                continue

            else:
                line.append(token)
                continue

        if len(line) > 0:
            lines.append(line)

        return lines
            

#END
