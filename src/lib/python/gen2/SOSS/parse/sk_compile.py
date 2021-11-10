#!/usr/bin/env python
#
# sk_compile.py -- Compile skeleton files to Python.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Nov  1 21:57:24 HST 2010
#]
#

import sys, os
import re, time
import StringIO

import Bunch
import ssdlog

from sk_common import ASTNode, skError
import sk_interp

class SkCompileError(skError):
    pass

        
# TODO: should this go in sk_common?
def get_subsys(obe_id, obe_mode):
    subsys = obe_id.upper() + '_' + obe_mode.upper()
    return subsys


##############################################################
# COMPILER
##############################################################

class SkCompiler(object):
    """
    """
    def __init__(self, sk_bank, logger, append_mode=False):
        """SkCompiler constructor.  (params) is a dict of the initial
        environment (variables & values) of the skcompiler.  (sk_bank) is
        used to lookup sk file ASTs and default parameters.
        """

        # Object that lets me look up parsed abstract commands
        self.sk_bank = sk_bank
        self.logger = logger
        self.append_mode = append_mode

        ## self.nop = ASTNode('nop')

        self.count = 1

        super(SkCompiler, self).__init__()
    

    def compile_skeleton(self, obe_id, obe_mode, abscmd):

        skbunch = self.sk_bank.lookup(obe_id, obe_mode, abscmd)

        subsys = get_subsys(obe_id, obe_mode)
        classname = '%s' % (abscmd.capitalize())

        # Initialize "global" vars used for compiling a skeleton
        self.sk_params = {}
        self.buf = StringIO.StringIO()
        if self.append_mode:
            self.buf.write("\n\n")
        self.buf.write("#\n# compile date: %s\n#\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        if not self.append_mode:
            self.buf.write("from skCompTask import *\n\n")
            self.buf.write("SUBSYS = %s\n\n" % (repr(subsys)))
        self.buf.write("class %s(skCompTask):\n\n" % (classname))

        self.skcompile_skeleton(skbunch.ast, classname=classname)
        return self.buf.getvalue()


    def skcompile(self, ast, indent=4):
        """Generic skcompile method.  Looks up the specific skcompiler for the
        ast and calls it.  If it does not have it's own special skcompiler
        then it is a generic ast.  Recurse through it and reconstruct the
        ast.
        """
        #self.logger.debug("SKCOMPILE: AST=%s\n\n" % str(ast))
        if not isinstance(ast, ASTNode):
            raise SkCompileError("Unexpected type in compiling: %s (%s)" % (
                str(ast), str(type(ast))))

        try:
            skcompile_method = getattr(self, 'skcompile_%s' % ast.tag)

            if not callable(skcompile_method):
                raise SkCompileError("Not a valid skcompile method '%s'" % ast.tag)

        except AttributeError:
            # ==> There is no function "skcompile_XXX" for the tag XXX of the ast.
            raise SkCompileError("No compilation method for AST=%s" % (str(ast)))

        try:
            return skcompile_method(ast, indent=indent)

        except AssertionError, e:
            raise SkCompileError(str(e))
        

    def _skcompile_exp(self, ast, info):
        """Compile an expression and return the string for the code.
        """
        self.logger.debug("skcompile_exp: ast=%s" % str(ast))
        assert isinstance(ast, ASTNode), \
               SkCompileError("Malformed expression AST: %s" % str(ast))

        if ast.tag == 'dyad':
            assert len(ast.items) == 3, \
                   SkCompilerError("Malformed dyad AST: %s" % str(ast))

            val1 = self._skcompile_exp(ast.items[0], info)
            val2 = self._skcompile_exp(ast.items[2], info)
            opr = ast.items[1]

            if opr in ('+', '-', '*', '/'):
                val1 = 'float(%s)' % val1
                val2 = 'float(%s)' % val2

            elif opr in ('AND', 'OR'):
                opr = opr.lower()

            return "(%s %s %s)" % (val1, opr, val2)

        elif ast.tag == 'monad':
            assert len(ast.items) == 2, \
                   SkCompileError("Malformed modad AST: %s" % str(ast))

            opr = ast.items[0]
            val1 = self._skcompile_exp(ast.items[1], info)

            if opr == '-':
                val1 = 'float(%s)' % val1

            elif opr == 'NOT':
                opr = opr.lower()

            return "(%s %s)" % (opr, val1)

        elif ast.tag == 'func_call':
            raise SkCompileError("Function calls not yet implemented: %s" % str(ast))
            func_name = ast.items[0].lower()
            tmp_vals = map(self.eval_num, ast.items[1].items[0])
            if func_name == 'sin':
                return math.sin(math.radians(tmp_vals[0]))
            if func_name == 'cos':
                return math.cos(math.radians(tmp_vals[0]))
            if func_name == 'tan':
                return math.tan(math.radians(tmp_vals[0]))
            raise skError("Unrecognized built in function: '%s'" % func_name)

        elif ast.tag == 'frame_id_ref':
            assert isinstance(ast.items[0], str), \
                   SkCompileError("Unrecognized frame id reference AST: %s" % (
                str(ast)))
            args = ast.items[0].split()
            assert (len(args) >= 2) and (len(args) < 4), \
                   SkCompileError("Unrecognized frame id reference AST: %s" % (
                str(ast.items)))
            
            ins = repr(args[0])
            typ = repr(args[1])
            if len(args) == 3:
                count = self.string_interpolate(args[2], info)
                return "self.get_frames(%s, %s, %s)" % (ins, typ, count)
            else:
                return "self.get_frame(%s, %s)" % (ins, typ)

        elif ast.tag == 'asnum':
            val1 = self._skcompile_exp(ast.items[0], info)
         
            return "float(%s)" % (val1)

        elif ast.tag == 'expression_list':
            raise SkCompileError("AST handling not yet implemented: %s" % str(ast))
            l = map(self.eval, ast.items[0])
            return l

        elif ast.tag == 'list':
            return self.string_interpolate(ast.items[0], info)

        elif ast.tag == 'param_list':
            res = []
            for ast in ast.items:
                res.append(self._skcompile_exp(ast, info))
            return ', '.join(res)

        elif ast.tag == 'key_value_pair':
            key = ast.items[0]
            val_s = self._skcompile_exp(ast.items[1], info)
            return '%s=%s' % (str(key), val_s)
            
        elif ast.tag in ('number', 'string'):
            return repr(ast.items[0])
        
        elif ast.tag in ('qstring', 'lstring'):
            return self.string_interpolate(ast.items[0], info)
        
        elif ast.tag == 'alias_ref':
            alias = ast.items[0]
            return self._resolve_alias(alias, info)

        elif ast.tag == 'id_ref':
            varname = ast.items[0]
            varname = varname.lower()
            return self._resolve_var(varname)
        
        elif ast.tag == 'reg_ref':
            raise SkCompileError("AST handling not yet implemented: %s" % str(ast))
            return self.registers.get(ast.items[0])

        else:
            # Everything else evaluates to itself
            raise SkCompileError("AST handling not yet implemented: %s" % str(ast))
            return ast
        
    def skcompile_exp(self, ast):
        self.logger.debug("skcompile_exp: ast=%s" % str(ast))
        info = Bunch.Bunch()
        return self._skcompile_exp(ast, info)

    def _resolve_var(self, varname):
        # If this variable name matches an abstract command (skeleton)
        # parameter, then reference the class variable, otherwise this
        # is a local variable
        varname = varname.lower()
        if self.sk_params.has_key(varname):
            return "self.params.%s" % (varname)
        else:
            return "self.params.%s" % (varname)
            #return varname

    def _resolve_alias(self, alias, info):
        aliasList = info.setdefault('aliasList', set([]))
        aliasList.add(alias)
        try:
            return info.aliasMap[alias]
        except Exception, e:
            return "self.fetchOne(%s)" % repr(alias)

    def string_interpolate(self, stg, info):

        def scan_special(buf, regex):
            match = re.match(regex, buf)
            if match:
                args = list(match.groups())
                buf = args.pop()
                return (buf, args)

            raise SkCompileError("Malformed string (interpolation): '%s'" % (stg))
        def i_frameid(*args):
            return "self.get_frame(%s)" % str(args)

        re_token = r'^([\w_][\w\d_\.]*)(.*)$'
        re_frame = r'^GET_F_NO\[([\w_][\w\d_\.]*)\s*([AQ])\](.*)$'

        spc_dict = { '&': (re_frame, i_frameid),
                     '!': (re_token, lambda alias: self._resolve_alias(alias,
                                                                       info)),
                     '$': (re_token, self._resolve_var),
                     # This should raise an error--we can't support interpolated regrefs
                     #'@': (re_token, i_reg),
                     }
        specials = spc_dict.keys()
        
        res = []
        iargs = []
        buf = stg

        try:
            # Iterate over buffer.  If a character is not a special one, just
            # append it to the output buffer.  Otherwise, scan the token and
            # call the "getter" function on it, appending the results to the
            # buffer.
            while len(buf) > 0:
                c = buf[0]
                buf = buf[1:]

                # Handle escaped specials.
                # TODO: is there a SOSS string escape char?
                if c == '\\':
                    if len(buf) > 0:
                        res.append(buf[0])
                        buf = buf[1:]
                    continue

                # If not a special character, then append to buffer and carry on
                if not c in specials:
                    res.append(c)
                    continue

                # Scan the special token and deal with it
                (regex, get_fn) = spc_dict[c]
                buf, args = scan_special(buf, regex)

                # Call the getter for this kind of token, convert to
                # a string and append to the result list
                val = get_fn(*args)
                iargs.append(str(val))
                res.append('%s')

        except Exception, e:
            raise SkCompileError("Error interpolating string '%s': %s" % (
                stg, str(e)))

        if len(iargs) == 0:
            return repr(stg)
        
        # Return the string made by concatenating all results
        res_str = ''.join(res)
        if res_str == '%s':
            res_str = iargs[0]
        else:
            res_str = '"""%s""" %% (%s)' % (res_str, ', '.join(iargs))
        #self.logger.debug("interpolation result is '%s'" % res_str)
        return res_str

    def is_aliasref(self, ast):
        return ast.tag == 'alias_ref'

    def get_value(self, ast):
        if ast.tag in ('number', 'string', 'qstring'):
            return ast.items[0]

        #if ast.tag in ('alias_ref',):
        #    return ast.items[0]

        if ast.tag in ('lstring',):
            return ast.items[0].strip().split()

        raise SkCompileError("Don't know how to render the constant '%s'" % (
            ast.tag))
        
    def skcompile_skeleton(self, ast, indent=4, classname=''):
        assert (ast.tag == 'skeleton') and (len(ast.items) == 2), \
               SkCompileError("Malformed skeleton AST: %s" % str(ast))

        (ast_params, ast_body) = ast.items

        pinfo = self._get_params(ast_params)
        # WARNING: SIDE_EFFECT
        self.sk_params = pinfo.paramDict
        
        s_indent = ' ' * indent
        ss_indent = ' ' * (indent+4)
        sss_indent = ' ' * (indent+8)

        self.buf.write('%sdef __init__(self, ' % s_indent)

        first_flg = True

        # Write constructor
        for varname in pinfo.paramList:
            value = pinfo.paramDict[varname]
            if not first_flg:
                self.buf.write(', ')
            self.buf.write('%s=%s' % (varname, repr(value)))
            first_flg = False
            
        self.buf.write('):\n')

        self.buf.write(' ' * (indent+4))
        self.buf.write('super(%s, self).__init__(' % (classname))
        self.buf.write('%s)\n' % ', '.join(map(lambda n: '%s=%s' % (n, n),
                                               pinfo.paramList)))

        assert (ast_body.tag == 'command_section') and (
            len(ast_body.items) == 3), \
            SkCompileError("Malformed command section AST: %s" % str(ast_body))

        # Extract the 3 sub-ASTs from the skeleton file body ast.
        (pre_ast, main_ast, post_ast) = ast_body.items

        # Write body
        # pre-processing part
        self.buf.write('\n')
        self.buf.write('%sdef do_pre(self):\n' % (s_indent))

        # TODO: do we need to create closures as parameters to abstract
        # commands?
        self.buf.write('%sself.thaw_closures()\n' % (ss_indent))

        if len(pinfo.aliasList) > 0:
            self.buf.write('%sself.get_param_aliases(%s)\n' % (ss_indent,
                                                               repr(pinfo.aliasList)))
        
        self.skcompile(pre_ast, indent=indent+4)
        self.buf.write('%spass\n' % (ss_indent))

        # main part
        self.buf.write('\n')
        self.buf.write('%sdef do_main(self):\n' % (s_indent))
        self.skcompile(main_ast, indent=indent+4)
        self.buf.write('%spass\n' % (ss_indent))

        # post-processing part
        self.buf.write('\n')
        self.buf.write('%sdef do_post(self):\n' % (s_indent))
        self.skcompile(post_ast, indent=indent+4)
        self.buf.write('%spass\n' % (ss_indent))
        
        
    def skcompile_nop(self, ast, indent=4):
        # NOTE: this is for the AST NOP appearing in a STATEMENT position
        #s_indent = ' ' * indent
        #self.buf.write('%spass\n' % s_indent)
        pass

    def skcompile_block(self, ast, indent=4):
        s_indent = ' ' * indent
        self.buf.write("%sself.enter_block()\n" % (s_indent))
        for ast in ast.items:
            self.skcompile(ast, indent=indent)

        self.buf.write("%sself.exit_block()\n" % (s_indent))
        
    def skcompile_cmdlist(self, ast, indent=4):
        assert (ast.tag == 'cmdlist'), \
            SkCompileError("Malformed command list AST: %s" % str(ast))
        self.skcompile_block(ast, indent=indent)
        
    def skcompile_sync(self, ast, indent=4):
        assert (ast.tag == 'sync'), \
            SkCompileError("Malformed sync AST: %s" % str(ast))
        self.skcompile(ast.items[0], indent=indent)
        
    def skcompile_async(self, ast, indent=4):
        assert (ast.tag == 'async'), \
            SkCompileError("Malformed async AST: %s" % str(ast))

        s_indent = ' ' * indent
        self.buf.write("%s@async(self)\n" % (s_indent))
        self.buf.write("%sdef fn%d():\n" % (s_indent, self.bumpcnt()))
        indent += 4

        ast = ast.items[0]
        self.skcompile(ast, indent=indent)
        
    def skcompile_star_if(self, ast, indent=4):
        """Skcompile a *IF statement.

        *IF <pred-exp>
            <then-clause>
        *ELIF <pred-exp>
            <then-clause>
        ...
        *ELSE
            <else-clause>
        *ENDIF

        AST is a variable number of 'cond' ribs (if-exp, then-exp).  Else
        clause is represented by a final (True, then-exp) cond rib.
        """
        assert ast.tag in ('if_list', 'star_if'), \
               SkCompileError("Malformed *IF/IF AST: %s" % str(ast))

        s_indent = ' ' * indent

        # Create a list of all the predicate expression ASTs
        astlist = []
        for cond_ast in ast.items:
            assert (cond_ast.tag == 'cond') and (len(cond_ast.items) == 2), \
                SkCompileError("Malformed cond rib in IF stmt: %s" % (
                str(cond_ast)))
            (pred_ast, then_ast) = cond_ast.items

            if pred_ast != True:
                astlist.append(pred_ast)

        # Optomize status fetch for this group
        info = self._optomize_exp(astlist, indent=indent)

        # Code generation for the IF
        kwd = 'if'
        for cond_ast in ast.items:
            # Form was already verified above
            (pred_ast, then_ast) = cond_ast.items
            
            if pred_ast == True:
                # ELSE clause
                self.buf.write("%selse:\n" % (s_indent))

            else:
                # No longer.  Could be dyad or monad...
                #assert pred_ast.tag == 'expression', ASTerr(pred_ast)

                pred_code = self._skcompile_exp(pred_ast, info)
                self.buf.write("%s%s %s:\n" % (s_indent, kwd, pred_code))

            self.skcompile(then_ast, indent=indent+4)

            kwd = 'elif'

    
    def skcompile_if_list(self, ast, indent=4):
        self.skcompile_star_if(ast, indent=indent)
        
    def skcompile_star_for(self, ast, indent=4):
        """Skcompile a *FOR statement.

        *FOR <num_exp> <var_lst> IN <val_lst>
          <cmd_lst>
        *ENDFOR

        Result is a command_block AST comprised of skcompiled cmd_lst
        nodes unrolled for as many iterations as in the loop.
        """
        assert (ast.tag == 'star_for') and (len(ast.items) == 4), \
               SkCompileError("Malformed *FOR AST: %s" % str(ast))
        
        (num_exp, var_lst, val_lst, cmdlst_ast) = ast.items

        s_indent = ' ' * indent
        # TODO: FIX FOR!!!
        ## self.buf.write("%sfor FIX in xrange(ME, UP):\n" % (s_indent))

        ## self.skcompile(cmdlst_ast, indent=indent+4)
        ## return
        
        # num_exp should evaluate to an integer.  This is the number of
        # iterations of the loop
        if num_exp.tag == 'number':
            loop_count = int(self.get_value(num_exp))
            s_max = repr(loop_count)
        elif num_exp.tag == 'id_ref':
            s_max = self._resolve_var(num_exp.items[0])
            loop_count = -1
        else:
            raise SkCompileError("*FOR <num> .. is not a number or var (%s)" % str(num_exp))

        # Evaluate list of variables
        assert var_lst.tag == 'idlist', \
               SkCompileError("*FOR stmt; malformed identifier list: %s" % (
                str(var_lst)))
        var_lst = map(lambda idref: self._resolve_var(idref.items[0]),
                      var_lst.items[0])

        # All items in result list should be strings
        #self.logger.debug("\n\nVARLIST IS %s\n\n" % str(var_lst))
        for item in var_lst:
            assert isinstance(item, str), \
                   SkCompileError("not a string item: %s" % str(item))
        var_lst_len = len(var_lst)

        assert var_lst_len == 1, \
               SkCompileError("Compilation of multiple variable lists!")

        # optional val_lst specifies a list of values for the variable
        # to take on for each unrolled iteration.  We default to 1..N
        if val_lst == None:
            # Can't have loop_count==0 AND missing values
            assert loop_count != 0, \
                   SkCompileError("Loop count is 0 AND no values supplied")

            self.buf.write("%sfor %s in xrange(1, %s+1):\n" % (
                s_indent, ', '.join(var_lst), s_max))

            self.skcompile(cmdlst_ast, indent=indent+4)
            return
        else:
            # <== A value list was specified
            assert val_lst.tag == 'list', \
                   SkCompileError("Malformed value list in *FOR (%s)" % str(val_lst))

            # Evaluate the values, which should result in a string
            vals = self.get_value(val_lst)
            assert isinstance(vals, str), \
                   SkCompileError("*FOR value list did not evaluate to a string: %s" % (
                str(vals)))

            # Split it by spaces
            val_lst = vals.split()

            val_lst_len = len(val_lst)
            assert var_lst_len <= val_lst_len, \
                   SkCompileError("*FOR stmt; variable/value list mismatch")
        
            # Values list must be an even multiple multiple of the variable list
            if (val_lst_len % var_lst_len) != 0:
                    raise SkCompileError("*FOR values/variable list size mismatch: (%d/%d)" % (val_lst_len, var_lst_len))

            # Match up the variable list with the value list
            # I'm sure there is an elegant list comprehension for this...
            qty = val_lst_len / var_lst_len
            tup = var_lst
            var_lst = []
            for i in xrange(qty):
                var_lst.extend(tup)

            self.logger.debug("var_lst=%s val_lst=%s" % (str(var_lst), str(val_lst)))
            assert len(var_lst) == len(val_lst), "variable/value list mismatch"

            # Loop count is allowed to be zero if there is a value list
            if loop_count == 0:
                loop_count = qty
        
        ## # Here's where the real unrolling takes place.  We produce a
        ## # command_block consisting of the set of unrolled iterations of
        ## # cmdlst_ast.
        ## astlist = []
        ## for i in xrange(loop_count):
        ##     # Set variables
        ##     index = i * var_lst_len

        ##     if index < val_lst_len:
        ##         for j in xrange(var_lst_len):
        ##             self.logger.debug("SETTING %s to %s" % (var_lst[index+j], val_lst[index+j]))
        ##             eval.set_var(var_lst[index+j], val_lst[index+j])

        ##     # skcompile body in env with updated variables
        ##     #self.logger.debug(str(eval.variables.variable_map))
        ##     body_ast = self._skcompile_merge(cmdlst_ast, eval)

        ##     # append into a giant mergeable list
        ##     astlist.append(body_ast)
        
        ## # return merged result
        ## #return ASTNode('block_merge', *astlist)
        ## return self.merge('block_merge', astlist)

        print "loop_count=%d qty=%d var_lst=%s val_list=%s" % (
            loop_count, qty, var_lst, val_lst)
    
    def skcompile_star_set(self, ast, indent=4):
        """Skcompile a *SET statement.

        *SET <param_list>

        Evaluate the parameter list and set the variables within the
        current skcompiler environment.
        """
        assert (ast.tag == 'star_set') and (len(ast.items) == 2), \
               SkCompileError("Malformed set AST: %s" % str(ast))

        ast_params = ast.items[0]
        assert (ast_params.tag == 'param_list'), \
               SkCompileError("Malformed parameter list to 'set' AST: %s" % str(ast))
        
        s_indent = ' ' * indent

        for ast_kvp in ast_params.items:
            assert (ast_kvp.tag == 'key_value_pair') and (
                len(ast_kvp.items) == 2), \
                   SkCompileError("Malformed key value pair AST: %s" % (
                str(ast_kvp)))

            (varname, val_ast) = ast_kvp.items
            var_s = self._resolve_var(varname)
            val_code = self.skcompile_exp(val_ast)
            self.buf.write("%s%s = %s\n" % (s_indent, var_s, val_code))


    def skcompile_star_sub(self, ast, indent=4):
        """Skcompile a *SUB statement.

        *SUB <cmd_exp> <param_list>

        Evaluate the <cmd_exp> to find the name of the abstract command
        being expanded.  Evaluate <param_list> to find the initial values
        for the parameters and skcompile it.  
        """
        assert (ast.tag == 'star_sub') and (len(ast.items) == 2), \
               SkCompileError("Malformed *SUB expression: %s" % str(ast))
        
        (ast_cmd_exp, ast_params) = ast.items

        # evaluate cmd_exp --> abs command name
        cmdname = self.get_value(ast_cmd_exp)
        assert isinstance(cmdname, str), \
               SkCompileError("command name does not evaluate to a string")
        
        s_indent = ' ' * indent
        
        ## pinfo = self._get_params(ast_params)
        # If there are status aliases in the parameter list, get them all in
        # one go now
        ## if len(pinfo.aliasList) > 0:
        ##     self.buf.write("%sfoo = self.fetch(%s)" % (s_indent,
        ##                                             repr(pinfo.statusDict)))
        
        info = self._optomize_exp([ast_params], indent=indent)

        self.buf.write("%sself.execab('%s'" % (s_indent,
                                               cmdname.capitalize()))

        params_code = self._skcompile_exp(ast_params, info).strip()
        if len(params_code) > 0:
            self.buf.write(", %s)\n" % params_code)
        else:
            self.buf.write(")\n")
    
    
    def skcompile_exec(self, ast, indent=4):
        assert (ast.tag == 'exec') and (len(ast.items) == 4), \
               SkCompileError("Badly formed EXEC ast: %s" % str(ast))

        (ast_subsys, ast_cmdname, ast_params, ast_resvar) = ast.items
        
        s_indent = ' ' * indent
        
        # Evaluate DD command parameters
        cmdname = self.get_value(ast_cmdname)
        subsys = self.get_value(ast_subsys)

        varname = None
        if ast_resvar != None:
            varname = self.get_value(ast_resvar)
            assert isinstance(varname, str), \
                   SkCompileError("Badly formed varname: %s" % str(varname))

        info = self._optomize_exp([ast_params], indent=indent)

        if varname:
            self.buf.write("%s%s = self.execdd('%s', '%s'" % (s_indent, varname,
                                                                subsys.upper(),
                                                                cmdname.capitalize()))
        else:
            self.buf.write("%sself.execdd('%s', '%s'" % (s_indent,
                                                           subsys.upper(),
                                                           cmdname.capitalize()))

        params_code = self._skcompile_exp(ast_params, info).strip()
        if len(params_code) > 0:
            self.buf.write(", %s)\n" % params_code)
        else:
            self.buf.write(")\n")
        

    def _optomize_exp(self, astlist, info=None, indent=4):

        s_indent = ' ' * indent

        if info == None:
            info = Bunch.Bunch(aliasList=set([]))

        for ast_exp in astlist:
            self._skcompile_exp(ast_exp, info)

        # If there are status aliases in the expression, get them all in
        # one go now
        if len(info.aliasList) > 0:
            aliasDict = {}.fromkeys(info.aliasList, None)
            self.buf.write("%s_stat = self.fetch(%s)\n" % (s_indent,
                                                           str(aliasDict)))
            srcList = [ "_stat['%s']" % alias for alias in info.aliasList ]
            info.aliasMap = dict(zip(info.aliasList, srcList))

        return info
        
    def _get_params(self, ast_params):
        assert ast_params.tag == 'param_list', \
               SkCompileError("Malformed parameter AST: %s" % str(ast_params))

        paramList = []
        paramDict = {}
        statusDict = {}
        aliasList = []
        res = Bunch.Bunch(paramList=paramList, paramDict=paramDict,
                          statusDict=statusDict, aliasList=aliasList)
        
        for ast_kvp in ast_params.items:
            assert (ast_kvp.tag == 'key_value_pair') and (
                len(ast_kvp.items) == 2), \
                   SkCompileError("Malformed key value pair AST: %s" % (
                str(ast_kvp)))

            # If this item is a status alias, add it to the dict of status
            # values that will need to be fetched
            (varname, val_ast) = ast_kvp.items
            if self.is_aliasref(val_ast):
                statusAlias = val_ast.items[0]
                statusDict[statusAlias] = '##NODATA##'
                value = None
                aliasList.append((varname, statusAlias))

            else:
                value = self.get_value(val_ast)

            paramList.append(varname)
            paramDict[varname] = value

        return res

    def bumpcnt(self):
        count = self.count
        self.count += 1
        return count



def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('sk_skcompile', options)

    if options.skdir:
        skdir = options.skdir
    else:
        try:
            skdir = os.path.join(os.environ['PYHOME'], 'SOSS', 'SkPara', 'sk')
        except KeyError:
            print "Please set your PYHOME environment variable"
            print "or specify the --skdir option"
            sys.exit(1)
        
    sk_bank = sk_interp.skBank(skdir, logger=logger)

    compiler = SkCompiler(sk_bank, logger,
                          append_mode=options.appendmode)

    obe_id = args[0].upper()
    obe_mode = args[1].upper()

    for cmd in args[2:]:
        print compiler.compile_skeleton(obe_id, obe_mode, cmd)
        compiler.append_mode = True

    return 0


if __name__ == "__main__":
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] <inst> <mode> [cmd ...]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--append", dest="appendmode", default=False,
                      action="store_true",
                      help="Tailor the output for appending to an existing file")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--skdir", dest="skdir",
                      help="Base directory of the skeleton files")
    optprs.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Turn on verbose output")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) < 2:
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
