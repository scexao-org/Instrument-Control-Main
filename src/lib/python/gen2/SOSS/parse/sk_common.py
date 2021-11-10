#
# support for sk interpretation -- common items
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Oct  8 15:31:28 HST 2012
#]
#
import sys, re
import SOSS.SOSSrpc as SOSSrpc

# top-level regular expression matching a skeleton file
# old style
sk_regex1 = re.compile(r"""^(?P<top>.*)\<Header\>(?P<hdr>.+)\</Header\>.*
\<Default_Parameter\>(?P<params>.+)\</Default_Parameter\>.*
\<Command\>(?P<cmd>.+)\</Command\>.*$""",
                   re.MULTILINE | re.IGNORECASE | re.DOTALL)
# new style
sk_regex2 = re.compile(r"^(?P<top>.*)\:HEADER\s+(?P<hdr>.*)"
":(DEFAULT_)?PARAMETER\s+(?P<params>.*)"
":COMMAND\s+(?P<cmd>.+)$",
                   re.MULTILINE | re.IGNORECASE | re.DOTALL)


class skError(Exception):
    pass

# For generating serial numbers, an atomic bump-type counter
seq_num = SOSSrpc.rpcSequenceNumber(0)

# HELPER FUNCTIONS

def mk_error(buf, errbnch, deltalines):
    """Make a formatted error message.
    """
    lines = buf.split('\n')
    res = [errbnch.errstr]

    if errbnch.lineno != 0:
        # Define the range of lines to be shown
        startline = max(1, errbnch.lineno - deltalines)
        endline = min(errbnch.lineno + deltalines, len(lines))

        # Print the lines
        n = startline
        while n <= endline:
            if n == errbnch.lineno:
                res.append("==>%5d: %s" % (n, lines[n-1]))
            else:
                res.append("   %5d: %s" % (n, lines[n-1]))

            n += 1

        return '\n'.join(res)

def get_skparts(buf):

    def process_match(match):
        # Count lines before command section to get accurate line number
        # reporting
        startline = len(match.group('top').split('\n')) - 1

        hdrbuf = match.group('hdr').strip()
        prmbuf = match.group('params').strip().replace('\t', ' ')
        cmdbuf = match.group('cmd').strip()

        return (hdrbuf, prmbuf, cmdbuf, startline)

    match = sk_regex1.match(buf)
    if match:
        return process_match(match)

    match = sk_regex2.match(buf)
    if match:
        return process_match(match)

    raise skError("sk file contents do not match expected format")


class ASTNode(object):

    def __init__(self, tag, *args, **kwargs):
        self.serial_num = seq_num.bump()
        self.tag = tag
        self.name = tag
        self.items = []
        for anItem in args:
            self.items.append(anItem)
        self.attributes = kwargs
  
    def append(self, item):
        self.items.append(item)
      
    def printAST(self):
        #TODO: something more readable
        factor = 4

        def pr(ast, level):
            sys.stdout.write(' ' * factor*level)
            if isinstance(ast, ASTNode):
                if len(ast.items) == 0:
                    print '(%s)' % (str(ast))
                else:
                    print '(%s):' % (ast.tag)
                    for item in ast.items:
                        pr(item, level+1)
            else:
                print '%s' % (str(ast))

        pr(self, 0)
    

    def AST2str(self):
        issue = IssueAST()
        return issue.issue(self)

    def __str__(self):
        return self.__repr__()

##     def __repr__(self):
##         return "ASTNode('%s', %s)" % (self.tag, ", ".join([repr(i) for i in self.items]))
    def __repr__(self):
        return "ASTNode('%s', %s)" % (self.tag, ", ".join([repr(i) for i in self.items]))


class Closure(object):
    def __init__(self, ast, eval):
        self.ast = ast
        self.eval = eval

    def thaw(self):
        return self.eval.eval(self.ast)


class IssueAST(object):
    """Take an AST and turn it back into a textual string representing
    the code.
    !!!NOTE!!!
    *** When you update sk_parser, you need to update this class
         accordingly!! ***
    """

    def issue(self, ast):
        if isinstance(ast, ASTNode):
            try:
                #print "issue_%s" % ast.tag
                method = getattr(self, 'issue_%s' % ast.tag)

            except AttributeError:
                method = self.issue_default

            return method(ast)

        elif isinstance(ast, Closure):
            return '~' + self.issue(ast.ast)
        
        else:
            #print "issue %s" % str(type(ast))
            return str(ast)

    def issue_sync(self, ast):
        return "%s ;" % (self.issue(ast.items[0]))

    def issue_async(self, ast):
        return "%s ," % (self.issue(ast.items[0]))

    def issue_exec(self, ast):
        p = map(self.issue, ast.items)
        if p[3] == 'None':
            return "EXEC %s %s %s" % (p[0], p[1], p[2])
        else:
            return "%s = EXEC %s %s %s" % (p[3], p[0], p[1], p[2])

    def issue_let(self, ast):
        p = map(self.issue, ast.items)
        return "LET %s %s" % (p[0], p[1])

    def issue_proc(self, ast):
        p = map(self.issue, ast.items)
        return "PROC %s(%s) %s" % (p[0], p[1], p[2])

    def issue_varlist(self, ast):
        p = map(self.issue, ast.items)
        return ", ".join(p)

    def issue_proc_call(self, ast):
        p = map(self.issue, ast.items)
        return "CALL %s(%s)" % (p[0], p[1])

    def issue_param_list(self, ast):
        params = map(self.issue, ast.items)
        return " ".join(params)

    def issue_key_value_pair(self, ast):
        return "%s=%s" % (ast.items[0].upper(), self.issue(ast.items[1]))

    def issue_nop(self, ast):
        return "NOP"

    def issue_number(self, ast):
        return str(ast.items[0])

    def issue_dyad(self, ast):
        return "%s %s %s" % (self.issue(ast.items[0]), ast.items[1],
                             self.issue(ast.items[2]))

    def issue_monad(self, ast):
        return "%s%s" % (ast.items[0], self.issue(ast.items[1]))

    def issue_alias_ref(self, ast):
        return "!%s" % (ast.items[0])

    def issue_id_ref(self, ast):
        return "$%s" % (ast.items[0])

    def issue_frame_id_ref(self, ast):
        return "&f_get_no[%s]" % (ast.items[0])

    def issue_reg_ref(self, ast):
        return "@%s" % (self.issue(ast.items[0]))

    def issue_string(self, ast):
        return ast.items[0].upper()

    def issue_qstring(self, ast):
        return '"%s"' % (ast.items[0])

    def issue_lstring(self, ast):
        return '[%s]' % (ast.items[0])

    def issue_term(self, ast):
        items = map(self.issue, ast.items)
        return ' '.join(items)

    def issue_asnum(self, ast):
        return "(%s)" % (self.issue(ast.items[0]))

    def issue_func_call(self, ast):
        items = map(self.issue, ast.items)
        return "%s(%s)" % (items[0], items[1])

    def issue_uminus(self, ast):
        return "-%s" % (self.issue(ast.items[0]))

    def issue_expression(self, ast):
        items = map(self.issue, ast.items)
        return ' '.join(items)

    def issue_expression2(self, ast):
        items = map(self.issue, ast.items)
        return ' '.join(items)

    def issue_expression_list(self, ast):
        items = map(self.issue, ast.items)
        return ', '.join(items)

    def issue_block(self, ast):
        stmts = map(self.issue, ast.items)
        return "{\n%s\n}" % ('\n'.join(stmts))

    def issue_block_merge(self, ast):
        stmts = map(self.issue, ast.items)
        return "m:{\n%s\n}" % ('\n'.join(stmts))

    def issue_if_list(self, ast):
        res = []
        for idx in range(len(ast.items)):
            cond_ast = ast.items[idx]
            if cond_ast.items[0] == True:
                res.append("ELSE")
                res.append("%s" % (self.issue(cond_ast.items[1])))
            else:
                if idx == 0:
                    res.append("IF %s" % (self.issue(cond_ast.items[0])))
                else:
                    res.append("ELIF %s" % (self.issue(cond_ast.items[0])))

                res.append("%s" % (self.issue(cond_ast.items[1])))

        res.append("ENDIF")
            
        return '\n'.join(res)

    def issue_cmdlist(self, ast):
        stmts = map(self.issue, ast.items)
        return "c:{\n%s\n}" % ('\n'.join(stmts))

    def issue_while(self, ast):
        pred, body = map(self.issue, ast.items)
        return "WHILE %s\n%s" % (pred, body)

    def issue_raise(self, ast):
        exp = self.issue(ast.items[0])
        return "RAISE %s" % (exp)

    def issue_skeleton(self, ast):
        (params, body) = map(self.issue, ast.items)
        # ??
        return body

    def issue_command_section(self, ast):
        (pre, body, post) = map(self.issue, ast.items)
        return ':START\n%s\n:MAIN_START\n%s\n:MAIN_END\n%s\n:END\n' % (
            pre, body, post)

    def issue_star_sub(self, ast):
        (cmd, params) = map(self.issue, ast.items)
        return '*SUB %s %s' % (cmd, params)

    def issue_set(self, ast):
        params = self.issue(ast.items[0])
        return 'SET %s' % (params)

    def issue_abscmd(self, ast):
        (cmd, params) = map(self.issue, ast.items)
        return '%s %s' % (cmd, params)

    # NOT handled yet: if_list, cond, star_if, star_set, star_for, idlist
    def issue_default(self, ast):
        if len(ast.items) == 0:
            return "AST(%s)" % (ast.tag)
        else:
            params = map(self.issue, ast.items)
            return "AST(%s:[%s])" % (ast.tag, ' '.join(params))


    
