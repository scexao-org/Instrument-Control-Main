#!/usr/bin/env python
#
# Legacy Skeleton File Handling.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 10 14:38:53 HST 2012
#]
#

"""
Legacy Skeleton File Handling.

To compare Gen2 SOSS compatibility mode decoding with SOSS decoding:

SOSS:
ossusr@mobs % setenv PATH /app/LOAD/DEBUG:$PATH
ossusr@mobs % setenv OSSS_CMDTBL <wherever your skeleton files are>
ossusr@mobs % cd /tmp
ossusr@mobs % ./OSSS_Decoder - 0 0 'GETOBJECT OBE_ID=IRCS OBE_MODE=IMAG_DM09_AONOG'

Gen2:
$ cd $PYHOME/SOSS/parse
$ ./sk_interp.py --skdir=../SkPara/sk --cmd='GETOBJECT OBE_ID=IRCS OBE_MODE=IMAG_DM09_AONOG'

"""

import sys, os, glob
import math, re, types

import Bunch
import logging, ssdlog

import sk_lexer
import sk_parser
import sk_common
from sk_common import ASTNode, skError, Closure

from cfg.INS import INSdata as INSconfig

class DecodeError(skError):
    pass

try:
    obshome = os.environ['OBSHOME']
    print "Warning: OBSHOME environment variable is not set!"
except KeyError:
    obshome = '.'
        
def ASTerr(ast):
    raise skError("AST does not match expected format: %s" % str(ast))

# TODO: should this go in sk_common?
def get_subsys(obe_id, obe_mode):

    subsys = obe_id.upper() + '_' + obe_mode.upper()
    return subsys


##############################################################
# SKELETON FILE LOOKUP, PARSING & CACHING
##############################################################

class skBank(object):
    """This kind of object abstracts the lookup and creation of the
    skeleton files ASTs.
    """
    
    def __init__(self, sk_basedir, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('sk.skbank')

        # Base directory of sk files
        self.sk_basedir = sk_basedir
        self.cache = Bunch.threadSafeBunch()

        self.lexer = sk_lexer.skScanner(logger=self.logger, debug=0,
                                        lextab='scan_tab')
        
        self.parser = sk_parser.skParser(self.lexer, logger=self.logger,
                                         debug=0,
                                         tabmodule='parser_tab')


    def preload_skfiles(self, obe_id, obe_mode):
        for skfile in glob.glob('%s/%s/sk/%s/*.sk' % (self.sk_basedir,
                                                      obe_id.upper(),
                                                      obe_mode.upper())):
            (abscmd, ext) = os.path.splitext(skfile)
            self.load_skfile(obe_id, obe_mode, abscmd)

        
    def load_skfile(self, obe_id, obe_mode, abscmd):
        """Locates, reads and parses the sk file identified by (obe_id),
        (obe_mode) and (abscmd).  The resulting AST is cached for future
        lookups. 
        """
        obe_id = obe_id.upper()
        obe_mode = obe_mode.upper()
        abscmd = abscmd.upper()
        
        skpath = '%s/%s/sk/%s/%s.sk' % (
            self.sk_basedir, obe_id, obe_mode, abscmd)

        # may raise skParseError or skLexError
        skbunch = self.parser.parse_skfile(skpath)

        # cache it
        self.cache[(obe_id, obe_mode, abscmd)] = skbunch

        return skbunch

        
    def lookup(self, obe_id, obe_mode, abscmd):
        """Locates, reads and parses the sk file identified by (obe_id),
        (obe_mode) and (abscmd).  Tries to get it from the cache, if possible.
        """
        obe_id = obe_id.upper()
        obe_mode = obe_mode.upper()
        abscmd = abscmd.upper()

        try:
            skbunch = self.cache[(obe_id, obe_mode, abscmd)]

        except KeyError:
            skbunch = self.load_skfile(obe_id, obe_mode, abscmd)

        return skbunch

    
    def invalidate(self, obe_id, obe_mode, abscmd):
        """Invalidates the cache entry for abscmd.
        """
        obe_id = obe_id.upper()
        obe_mode = obe_mode.upper()
        abscmd = abscmd.upper()

        try:
            del self.cache[(obe_id, obe_mode, abscmd)]

        except KeyError:
            # was not in the cache, apparently
            pass

    
##############################################################
# EXPRESSION EVALUATOR
##############################################################

def make_closure(ast, eval):

    if not isinstance(ast, ASTNode):
        return ast

    # optomize away closures for simple expressions
    if ast.tag in ('number', 'string'):
        return ast.items[0]

    return Closure(ast, eval)

        
class LazyDict(dict):
    def __getitem__(self, key):
        val = super(LazyDict, self).__getitem__(key)
        if isinstance(val, Closure):
            return val.thaw()
        else:
            return val


count = 1
class VariableResolver(object):
    def __init__(self, params):
        global count
        self.variable_map = Bunch.caselessDict(params)
        self.count = count
        count += 1
        
    def set(self, var, val, nonew=False):
        if nonew and (not self.variable_map.has_key(var)):
            raise skError("Variable does not exist in scope: '%s'" % (var))
        self.variable_map[var] = val       

    def setAll(self, varDict, nonew=False):
        if nonew:
            diff = set(varDict.keys()).difference(set(self.variable_map.keys()))
            if diff:
                raise skError("Variables do not exist in scope: %s" % (
                        str(list(diff))))
                
        self.variable_map.update(varDict)       

    def get(self, var):
        try:
            val = self.variable_map[var]

        except KeyError:
            raise skError("Variable does not exist in scope: '%s'" % var)

        if not isinstance(val, Closure):
            return val

        val = val.thaw()

        return val
            
    def getAST(self, var):
        #print "fetch(%s); vars=%s" % (var, str(self.variable_map))
        try:
            val = self.variable_map[var]

        except KeyError:
            raise skError("Variable does not exist in scope: '%s'" % var)

##         if not isinstance(val, Closure):
##             return val

##         #print "Closure ast: %s" % str(val.ast)
##         return val.ast
        return val
            
    def clone(self):
        return VariableResolver(self.variable_map)

    
class RegisterResolver(object):
    def __init__(self):
        self.special_keys = ['SYSTEM', 'USER', 'COMMAND', 'STATUS']
        rib = Bunch.caselessDict()
        self.ribs = [ rib ]
        
    def get(self, key):
        if key in self.special_keys:
            # These eventually get resolved in the ParaValidator
            return '@' + key

        for rib in self.ribs:
            if rib.has_key(key):
                return rib[key]

        raise skError("Variable accessed before assignment: '@%s'" % (key))

    def set(self, **kwdargs):
        for key, val in kwdargs.items():
            for rib in self.ribs:
                if rib.has_key(key):
                    rib[key] = val
                    continue
            rib = self.ribs[0]
            rib[key] = val
                
    def push(self, params):
        rib = Bunch.caselessDict(params)
        self.ribs.insert(0, rib)

    def pop(self):
        self.ribs.pop(0)

    def clone(self):
        rr = RegisterResolver()
        rr.ribs = self.ribs
        return rr

class StatusResolver(object):
    def __init__(self, statusObj):
        self.statusObj = statusObj
        
    def get(self, alias):
        return self.statusObj.fetchOne(alias)
    
class FrameSource(object):
    def __init__(self, frameObj):
        self.frameObj = frameObj
        
    def get(self, *args):

        if len(args) == 3:
            (instname, frametype, count) = args
            if count != None:
                count = int(count)

        elif len(args) == 2:
            (instname, frametype) = args
            count = None

        else:
            frames = "Bad arguments to get_f_no: %s" % str(args)
            raise skError(str(frames))
    
        if count == None:
            # Should return one frame
            frames = self.frameObj.getFrames(instname, frametype, 1)
            return frames[0]
        else:
            frames = self.frameObj.getFrames(instname, frametype, count)
            return '%s:%04d' % (frames[0], len(frames))
    
class MockRegisterResolver(object):
    def get(self, alias):
        raise skError("Illegal register fetch in decoding!")

class MockFrameSource(object):
    def __init__(self):
        self.count = 1
        self.insconfig = INSconfig()

    def get(self, *args):
        if len(args) == 3:
            (insname, frametype, count) = args
            count = int(count)
            inscode = self.insconfig.getCodeByName(insname)
            frameid = ('%-3.3s%1.1s%08.8d:%04.4d' % (
                inscode, frametype, self.count, count))
        elif len(args) == 2:
            (insname, frametype) = args
            inscode = self.insconfig.getCodeByName(insname)
            frameid = ('%-3.3s%1.1s%08.8d' % (
                inscode, frametype, self.count))
            count = 1
        else:
            raise DecodeError("Bad arguments to get_f_no: %s" % str(args))

        self.count += count
        return frameid

class MockStatusResolver(object):
    def __init__(self, statusDict):
        self.statusDict = statusDict
    def get(self, alias):
        try:
            return self.statusDict[alias]
        except KeyError:
            raise skError("Illegal status fetch (%s) in decoding!" % (
                alias))


class Evaluator(object):
    """Expressions need to be evaluated run time.  This class is a utility
    to evaluate the expression ast and return the value.
    """
    def __init__(self, variable_resolver, register_resolver, status_resolver,
                 frame_id_source, logger):
        self.variables = variable_resolver
        self.registers = register_resolver
        self.status = status_resolver
        self.frame_id_source = frame_id_source
        self.logger = logger

        re_token = re.compile(r'^([\w_][\w\d_\.]*)(.*)$')
        re_frame = re.compile(r'^GET_F_NO\[([\w_][\w\d_\.]*)\s*([AQ][789]?)\s*(\d+)?\s*\](.*)$',
                              re.IGNORECASE)

        self.spc_dict = { '&': (re_frame, self.frame_id_source.get),
                          '!': (re_token, self.status.get),
                          '$': (re_token, self.variables.get),
                          # This should raise an error--we can't support interpolated regrefs
                          '@': (re_token, self.registers.get),
                          }
    
    def set_var(self, var, val, nonew=False):
        #self.logger.debug("set %s=%s" % (var, str(val)))
        self.variables.set(var, val, nonew=nonew)

    def set_vars(self, vars_dict, nonew=False):
        self.variables.setAll(vars_dict, nonew=nonew)

    def getAST(self, var):
        return self.variables.getAST(var)

    def isTrue(self, val):
        # is Python interpretation of True OK?
        return val

    def eval(self, ast):
        self.logger.debug("eval: ast=%s" % str(ast))
        if isinstance(ast, Closure):
            return ast.thaw()

        if not isinstance(ast, ASTNode):
            return ast

        elif ast.tag == 'dyad':
            assert len(ast.items)==3, ASTerr(ast)

            val1 = self.eval(ast.items[0])
            val2 = self.eval(ast.items[2])
            opr = ast.items[1]

            if opr == '+':
                return (float(val1) + float(val2))
            elif opr == '-':
                return (float(val1) - float(val2))
            elif opr == '*':
                return (float(val1) * float(val2))
            elif opr == '/':
                return (float(val1) / float(val2))
            elif opr == '==':
                return (val1 == val2)
            elif opr == '>':
                return (val1 > val2)
            elif opr == '<':
                return (val1 < val2)
            elif opr == '>=':
                return (val1 >= val2)
            elif opr == '<=':
                return (val1 <= val2)
            elif opr == '!=':
                return (val1 != val2)
            elif opr == 'AND':
                return (self.isTrue(val1) and self.isTrue(val2))
            elif opr == 'OR':
                return (self.isTrue(val1) or self.isTrue(val2))
            else:
                raise skError("Unrecognized expression operator: '%s'" % opr)

        elif ast.tag == 'monad':
            assert len(ast.items)==2, ASTerr(ast)

            opr = ast.items[0]
            val1 = self.eval(ast.items[1])

            if opr == '-':
                return -(float(val1))
            elif opr == 'NOT':
                return (not self.isTrue(val1))
            else:
                raise skError("Unrecognized expression operator: '%s'" % opr)

        #elif ast.tag == 'uminus':
        #    return self.eval_num(ast.items[0]) * -1

        #elif ast.tag == 'param_list':
        #    return self.eval_params(ast)
        
        elif ast.tag == 'func_call':
            func_name = ast.items[0].lower()
            explst, kwdargs = self.eval_args(ast.items[1])
            if func_name == 'sin':
                tmp_vals = map(float, explst)
                return math.sin(math.radians(tmp_vals[0]))
            elif func_name == 'cos':
                tmp_vals = map(float, explst)
                return math.cos(math.radians(tmp_vals[0]))
            elif func_name == 'tan':
                tmp_vals = map(float, explst)
                return math.tan(math.radians(tmp_vals[0]))
            elif func_name == 'int':
                return int(explst[0])
            elif func_name == 'float':
                return float(explst[0])
            elif func_name == 'frame':
                return self.frame_id_source.get(*explst)
            elif func_name == 'format':
                return explst[0] % tuple(explst[1:])
            raise skError("Unrecognized built in function: '%s'" % func_name)

        elif ast.tag == 'frame_id_ref':
            s = self.eval_string_interpolate(ast.items[0])
            args = s.split()
            return self.frame_id_source.get(*args)

        elif ast.tag == 'asnum':
            return self.eval_num(ast.items[0])

        elif ast.tag == 'expression_list':
            l = map(self.eval, ast.items)
            return l

        elif ast.tag == 'list':
            return self.eval_string_interpolate(ast.items[0])

        elif ast.tag in ('number', 'string'):
            return ast.items[0]
        
        elif ast.tag in ('qstring', 'lstring'):
            if hasattr(ast, 'cls'):
                return ast.cls.thaw()
            return self.eval_string_interpolate(ast.items[0])
        
        elif ast.tag == 'alias_ref':
            alias = ast.items[0]
            val = self.status.get(alias)
            self.logger.debug("eval %s -> %s" % (alias, str(val)))
            return val

        elif ast.tag == 'id_ref':
            return self.variables.get(ast.items[0])
        
        elif ast.tag == 'reg_ref':
            return self.registers.get(ast.items[0])
        
        elif ast.tag == 'proc_call':
            regref, args_ast = ast.items
            # get function
            fn = self.registers.get(regref[1:])
            # eval parameters
            args, kwdargs = self.eval_args(args_ast)

            return fn(**kwdargs)

        else:
            # Everything else evaluates to itself
            return ast
        

    def eval_num(self, ast):
        str_val = self.eval(ast)
        return float(str_val)

    def _mkproc(self, varDict, body_ast):
        def _foo(**kwdargs):
            return (self, varDict, body_ast)
        return _foo
        
    
    def _scan_special(self, buf, regex):
        match = regex.match(buf)
        if match:
            args = list(match.groups())
            buf = args.pop()
            return (buf, args)

        raise skError("Malformed string (interpolation): '%s'" % (stg))

    def eval_string_interpolate(self, stg, vars_only=False):
        """Evaluate a string ast in the current environment.
        Returns a python string with values interpolated.
        """

        if vars_only:
            specials = ['$', '&']
        else:
            specials = self.spc_dict.keys()
        
        res = []
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
                (regex, get_fn) = self.spc_dict[c]
                buf, args = self._scan_special(buf, regex)

                # Call the getter for this kind of token, convert to
                # a string and append to the result list
                val = get_fn(*args)
                res.append(str(val))

        except Exception, e:
            raise skError("Error interpolating string '%s': %s" % (
                stg, str(e)))

        # Return the string made by concatenating all results
        res_str = ''.join(res)
        #self.logger.debug("interpolation result is '%s'" % res_str)
        return res_str


    def close_params(self, ast):
        """Evaluate a parameter list ast in the current environment.
        Returns a dictionary of all the variables and their closures.
        """

        assert ast.tag == 'param_list', ASTerr(ast)

        # Iterate over subitems, each of which should be a var=exp pair.
        # Evaluate all expressions and assign values to variables in the
        # result dictionary.
        # ?res = caselessDict()
        # UPDATE: Currently, parser is delivering param_lists with lower-case
        # converted identifiers
        res = LazyDict()

        for keyval in ast.items:
            assert keyval.tag == 'key_value_pair', ASTerr(keyval)

            (var, val_ast) = keyval.items
            assert type(var) == types.StringType, ASTerr(keyval)

            val = make_closure(val_ast, self)

            res[var] = val
            #res[var.lower()] = val

        return res


    def eval_params(self, ast):
        """Evaluate a parameter list ast in the current environment.
        Returns a dictionary of all the variables and their values.
        """

        assert ast.tag in ('param_list', 'kwd_params'), ASTerr(ast)

        # Iterate over subitems, each of which should be a var=exp pair.
        # Evaluate all expressions and assign values to variables in the
        # result dictionary.
        # ?res = caselessDict()
        # UPDATE: Currently, parser is delivering param_lists with lower-case converted
        # identifiers
        res = {}

        for keyval in ast.items:
            assert keyval.tag == 'key_value_pair', ASTerr(keyval)

            (var, val_ast) = keyval.items
            assert type(var) == types.StringType, ASTerr(keyval)

            val = self.eval(val_ast)

            res[var] = val
            #res[var.lower()] = val

        return res


    def eval_args(self, ast):
        """Evaluate an argument list ast in the current environment.
        Returns a tuple of any non-keyword parameters and dictionary of all
        keyword parameters.
        """

        assert ast.tag == 'arg_list', ASTerr(ast)

        resList = []
        resDict = {}

        for subast in ast.items:
            if subast.tag == 'key_value_pair':
                (var, val_ast) = subast.items
                assert type(var) == types.StringType, ASTerr(subast)

                resDict[var] = self.eval(val_ast)
            else:
                resList.append(self.eval(subast))
        return resList, resDict


    def set_params(self, ast, close=False):
        """Evaluate a parameter list ast in the current environment.
        Sets all the variables in the current environment their values.
        """

        assert ast.tag == 'param_list', ASTerr(ast)

        # Iterate over subitems, each of which should be a var=exp pair.
        # Evaluate all expressions and assign values to variables.
        for keyval in ast.items:
            assert keyval.tag == 'key_value_pair', ASTerr(keyval)

            (var, val_ast) = keyval.items
            assert type(var) == types.StringType, ASTerr(keyval)

            if close:
                val = make_closure(val_ast, self)
                
            else:
                val = self.eval(val_ast)

            self.set_var(var, val)


    def clone(self, inherit_vars=True):
        """Make a clone of ourself, except having a new set of variables.
        """
        if inherit_vars:
            variable_resolver = self.variables.clone()
            
        else:
            variable_resolver = VariableResolver({})
        register_resolver = self.registers.clone()

        evaluator = Evaluator(variable_resolver, register_resolver,
                              self.status, self.frame_id_source,
                              self.logger)
        return evaluator

        
##############################################################
# DECODER
##############################################################

class Decoder(object):
    """
    NOTES.
    [1] This should expand to nothing, but our decoder design always returns
    an ast, so NOP is used.

    TODO.
    [ ] Currently the <Header>...</Header> area is ignored.
    
    """
    def __init__(self, evaluator, sk_bank, logger):
        """Decoder constructor.  (params) is a dict of the initial
        environment (variables & values) of the decoder.  (sk_bank) is
        used to lookup sk file ASTs and default parameters.
        """

        # Evaluator for all external entities
        self.eval = evaluator
        # Object that lets me look up parsed abstract commands
        self.sk_bank = sk_bank
        self.logger = logger

        self.nop = ASTNode('nop')
        
        super(Decoder, self).__init__()
    

    def decode(self, ast, eval):
        """Generic decode method.  Looks up the specific decoder for the
        ast and calls it.  If it does not have it's own special decoder
        then it is a generic ast.  Recurse through it and reconstruct the
        ast.
        """
        #self.logger.debug("DECODE: AST=%s\n\n" % str(ast))
        if isinstance(ast, Closure):
            return ast
        
        if not isinstance(ast, ASTNode):
            raise DecodeError("Unexpected type in decoding: %s (%s)" % (
                str(ast), str(type(ast))))

        try:
            decode_method = getattr(self, 'decode_%s' % ast.tag)

            if not callable(decode_method):
                raise DecodeError("Not a valid decode method '%s'" % ast.tag)

        except AttributeError:
            # ==> There is no function "decode_XXX" for the tag XXX of the ast.
            # Therefore, simply recurse over the subtrees and reconsitute the
            # results.
            try:
                return self.recode(ast, eval)

            except AssertionError, e:
                raise DecodeError(str(e))

        try:
            return decode_method(ast, eval)

        except AssertionError, e:
            raise DecodeError(str(e))
        
    
    def merge(self, tag, astlist, **astattrs):

        newitems = []
        for item in astlist:
            if type(item) != ASTNode:
                newitems.append(item)

            else:
                if item.tag == 'block_merge':
                    newitems.extend(item.items)
                else:
                    if (item.tag in ('async', 'sync', 'block',
                                     'block_merge', 'cmdlist')
                        ) and (len(item.items) == 0):
                        pass
                    else:
                        newitems.append(item)

        # if new item is a code block of some kind, but contains no
        # statements, then change it to a block_merge to be merged
        # into the parent ast node
        if (tag in ('async', 'sync', 'block', 'cmdlist')) and \
               (len(newitems) == 0):
            return ASTNode('block_merge')
            
        return ASTNode(tag, *newitems, **astattrs)


    def recode(self, ast, eval):
        """Iterate over items in this ast.  For each sub-ast, decode it;
        other items are taken verbatim.  Form a new item list and use
        it to recreate an ASTNode of the original type.
        """
        #self.logger.debug("RECODE: tag=%s" % ast.tag)

        merge_ok = (ast.tag in ('block', 'block_merge', 'cmdlist'))

        newitems = []
        for item in ast.items:
            if type(item) == ASTNode:
                new_ast = self.decode(item, eval)
                
                if isinstance(new_ast, ASTNode) and \
                        (new_ast.tag == 'block_merge') and merge_ok:
                    newitems.extend(new_ast.items)
                else:
                    newitems.append(new_ast)
            else:
                newitems.append(item)

        # if new item is a code block of some kind, but contains no
        # statements, then change it to a block_merge to be merged
        # into the parent ast node
        if (ast.tag in ('async', 'sync', 'block', 'cmdlist')) and \
           (len(newitems) == 0):
            #return self.nop
            return ASTNode('block_merge')
            
        return ASTNode(ast.tag, *newitems, **ast.attributes)


    def decode_id_ref(self, ast, eval):
        """Decode a identifier reference.
        """
        assert ast.tag == 'id_ref', ASTerr(ast)

        var = ast.items[0]

        # If this is a variable capturing the result of a DD command
        # then don't decode it as it will be used at execution time
        if re.match(r'^RET\d?$', var):
            return ast
        
        #print "Getting VAR=%s" % var
        res = eval.getAST(var)
        #print "RES= %s" % str(res)

        if isinstance(res, int) or isinstance(res, float):
            return ASTNode('number', res)

        if isinstance(res, str):
            return ASTNode('string', res)

        # NOP?
        #print "RES= %s" % str(res)

##         if type(res) != ASTNode:
##             raise DecodeError("Unexpected eval result in decoding type: %s='%s' (%s)" % (
##                 var, str(res), str(type(res))))
        if type(res) != Closure:
            raise DecodeError("Unexpected eval result in decoding type: %s='%s' (%s)" % (
                var, str(res), str(type(res))))

        # <-- res is an ASTNode
        return res
    
    
    def decode_frame_id_ref(self, ast, eval):
        """Decode a frame allocation reference.
        """
        assert ast.tag == 'frame_id_ref', ASTerr(ast)

        # In SOSS, frame id allocations are done in decoding!
        # uncomment this to reserve allocations until execution time
##         res = eval.eval_string_interpolate(ast.items[0], vars_only=True)
##         if isinstance(res, str):
##             return ASTNode('frame_id_ref', res)

        # comment this to reserve allocations until execution time
        res = eval.eval(ast)
        if isinstance(res, str):
            return ASTNode('string', res)

        name = ast.items[0]
        raise DecodeError("Error decoding frame id reference: %s='%s' (%s)" % (
            name, str(res), str(type(res))))

    
    def _decode_string(self, ast, eval):
        """Decode a string interpolation.
        """

#         cls = make_closure(ast, eval.clone())

#         ast = ASTNode(ast.tag, ast.items[0])
#         ast.cls = cls
#         return ast
    
        # Only expand variable references in strings in the decoding stage
        res = eval.eval_string_interpolate(ast.items[0], vars_only=True)

        if isinstance(res, str):
            return ASTNode(ast.tag, res)

        name = ast.items[0]
        raise DecodeError("Don't know how to decode type: %s='%s' (%s)" % (
            name, str(res), str(type(res))))

    def decode_number(self, ast, eval):
        """Normal number decodes to self"""
        assert ast.tag == 'number', ASTerr(ast)
        return ast
    
    def decode_string(self, ast, eval):
        """Normal unquoted string decodes to self"""
        assert ast.tag == 'string', ASTerr(ast)
        #return self._decode_string(ast, eval)
        return ast
    
    def decode_qstring(self, ast, eval):
        """Quoted string"""
        assert ast.tag == 'qstring', ASTerr(ast)
        return self._decode_string(ast, eval)
    
    def decode_lstring(self, ast, eval):
        """List string"""
        assert ast.tag == 'lstring', ASTerr(ast)
        return self._decode_string(ast, eval)

    
    def decode_star_if(self, ast, eval):
        """Decode a *IF statement.

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
        assert ast.tag == 'star_if', ASTerr(ast)
        
        # Iterate over the set of cond ribs, decode the first then-part
        # for whose predicate evaluates to true.
        for cond_ast in ast.items:
            assert cond_ast.tag == 'cond', ASTerr(cond_ast)

            assert len(cond_ast.items) == 2, ASTerr(cond_ast)
            (pred_ast, then_ast) = cond_ast.items

            if pred_ast == True:
                # ELSE clause
                return self._decode_merge(then_ast, eval)
            
            # No longer.  Could be dyad or monad...
            #assert pred_ast.tag == 'expression', ASTerr(pred_ast)

            res = eval.eval(pred_ast)
            if eval.isTrue(res):
                return self._decode_merge(then_ast, eval)

        # See Note [1]
        #return self.nop
        return ASTNode('block_merge')

    
    def decode_star_for(self, ast, eval):
        """Decode a *FOR statement.

        *FOR <num_exp> <var_lst> IN <val_lst>
          <cmd_lst>
        *ENDFOR

        Result is a command_block AST comprised of decoded cmd_lst
        nodes unrolled for as many iterations as in the loop.
        """
        assert ast.tag == 'star_for', ASTerr(ast)
        assert len(ast.items) == 4, ASTerr(ast)
        
        (num_exp, var_lst, val_lst, cmdlst_ast) = ast.items

        # num_exp should evaluate to an integer.  This is the number of
        # iterations of the loop, and specifies how many times the cmdlist
        # code is unrolled
        loop_count = int(eval.eval(num_exp))
        try:
            assert type(loop_count) == int, ASTerr(num_exp)

        except AssertionError:
            raise DecodeError("*FOR <num> .. is not a number (%s)" % str(loop_count))

        # optional val_lst specifies a list of values for the variable
        # to take on for each unrolled iteration.  We default to 1..N
        if val_lst == None:
            # Can't have loop_count==0 AND missing values
            assert loop_count != 0, "Loop count is 0 AND no values supplied"
            
            val_lst = range(loop_count+1)
            val_lst.pop(0)

        else:
            # <== A value list was specified

            # Evaluate the values, which should result in a string
            vals = eval.eval(val_lst)
            assert type(vals) == types.StringType, "values did not evaluate to a string"

            # Split it by spaces
            val_lst = vals.split()

        val_lst_len = len(val_lst)

        # Evaluate list of variables
        assert var_lst.tag == 'idlist', ASTerr(var_lst)
        var_lst = map(eval.eval, var_lst.items[0])

        # All items in result list should be strings
        #self.logger.debug("\n\nVARLIST IS %s\n\n" % str(var_lst))
        for item in var_lst:
            assert type(item) == types.StringType, "not a string item"

        var_lst_len = len(var_lst)

        assert var_lst_len <= val_lst_len, "variable/value list mismatch"
        
        # Values list must be an even multiple multiple of the variable list
        if (val_lst_len % var_lst_len) != 0:
                raise DecodeError("*FOR values/variable list size mismatch: (%d/%d)" % (val_lst_len, var_lst_len))

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
        
        # Here's where the real unrolling takes place.  We produce a
        # command_block consisting of the set of unrolled iterations of
        # cmdlst_ast.
        astlist = []
        for i in xrange(loop_count):
            # Set variables
            index = i * var_lst_len

            if index < val_lst_len:
                for j in xrange(var_lst_len):
                    self.logger.debug("SETTING %s to %s" % (var_lst[index+j], val_lst[index+j]))
                    eval.set_var(var_lst[index+j], val_lst[index+j])

            # decode body in env with updated variables
            #self.logger.debug(str(eval.variables.variable_map))
            body_ast = self._decode_merge(cmdlst_ast, eval)

            # append into a giant mergeable list
            astlist.append(body_ast)
        
        # return merged result
        #return ASTNode('block_merge', *astlist)
        return self.merge('block_merge', astlist)

    
    def decode_star_set(self, ast, eval):
        """Decode a *SET statement.

        *SET <param_list>

        Evaluate the parameter list and set the variables within the
        current decoder environment.
        """
        assert ast.tag == 'star_set', ASTerr(ast)
        assert len(ast.items) == 2, ASTerr(ast)

        params_ast = ast.items[0]
        close = (ast.items[1] != None)
        
        # Decode parameter list--should be no vars left afterward
        params = self._decode_params(params_ast, eval)

        #res = eval.set_params(params_ast, close=delay_eval)
        for var, val_ast in params.items():
            # if they specified any -ALIASOFF we'll delay evaluation
            if close:
                val = make_closure(val_ast, eval)
                
            else:
                val = eval.eval(val_ast)

            params[var] = val

        eval.set_vars(params)

        # See Decoder class Note [1]
        #return self.nop
        return ASTNode('block_merge')


##     def decode_skeleton(self, ast, eval):
##         """Decode a skeleton file ast.
##         """
##         assert ast.tag == 'skeleton', ASTerr(ast)
##         assert len(ast.items) == 2, ASTerr(ast)
        
##         (ast_params, ast_body) = ast.items

##         # Get new evaluator with empty variables
##         new_eval = eval.clone(inherit_vars=False)
##         #new_eval = self.eval.clone(inherit_vars=True)

##         # Set default parameters into the evaluator
##         new_eval.set_params(ast_params)

##         # Decode the commands AST
##         new_ast = self.decode(ast_body, new_eval)

##         # Q: Is ast_params left unchanged by decoding?  Assume so for now..
        
##         return ASTNode('skeleton', ast_params, new_ast)

        
    def decode_star_sub(self, ast, eval):
        """Decode a *SUB statement.

        *SUB <cmd_exp> <param_list>

        Evaluate the <cmd_exp> to find the name of the abstract command
        being expanded.  Evaluate <param_list> to find the initial values
        for the parameters and decode it.  
        """
        assert ast.tag == 'star_sub', ASTerr(ast)
        assert len(ast.items) == 2, ASTerr(ast)
        
        (ast_cmd_exp, ast_params) = ast.items

        # evaluate cmd_exp --> abs command name
        cmdname = eval.eval(ast_cmd_exp)
        assert type(cmdname) == types.StringType, "command name does not evaluate to a string"
        
        # Decode actual parameters to abstract command call
        # should be no vars left after this
        actuals = self._decode_params(ast_params, eval)

        # Check for presence of special OBE_ID and OBE_MODE parameters
        try:
            obe_id_ast = actuals['obe_id']
        except KeyError:
            raise DecodeError("No parameter set: OBE_ID")
        try:
            obe_mode_ast = actuals['obe_mode']
        except KeyError:
            raise DecodeError("No parameter set: OBE_MODE")

        # Remove these two from the actuals (? is this correct?)
        del actuals['obe_id']
        del actuals['obe_mode']
        
        # Evaluate OBE_ID and OBE_MODE
        obe_id = eval.eval(obe_id_ast)
        assert type(obe_id) == types.StringType, "OBE_ID does not evaluate to a string"
        obe_mode = eval.eval(obe_mode_ast)
        assert type(obe_mode) == types.StringType, "OBE_MODE does not evaluate to a string"

        # Make closures of the actuals
        #cur_eval = eval.clone()
        cur_eval = eval
        for (var, form) in actuals.items():
            actuals[var] = make_closure(form, cur_eval)

        # Look up the skeleton file from our sk_bank
        skbunch = self.sk_bank.lookup(obe_id, obe_mode, cmdname)
        if skbunch.errors > 0:
            # TODO: include verbose error string in this error
            raise DecodeError("%d errors parsing referent skeleton file '%s'" % (
                skbunch.errors, skbunch.filepath))

        ast = skbunch.ast
        assert ast.tag == 'skeleton', ASTerr(ast)
        assert len(ast.items) == 2, ASTerr(ast)
        
        (ast_default_params, ast_body) = ast.items

        # Get new evaluator with empty variables
        new_eval = eval.clone(inherit_vars=False)

        # Decode default parameters for abstract command
        # should be no vars left after this
        params = self._decode_params(ast_default_params, new_eval)

        # Make closures of them
        for (var, form) in params.items():
            params[var] = make_closure(form, new_eval)
        #print "Defaults:", params

        # Now substitute actuals overriding defaults as necessary
        #print "Substituting:", actuals.keys()
        params.update(actuals)
        #print "Final:", params

        # Store decoded forms into new evaluator
        new_eval.set_vars(params)

        # Decode the skeleton file body in the new environment
        new_ast_body = self.decode(ast_body, new_eval)
        
        assert new_ast_body.tag == 'command_section', ASTerr(new_ast_body)
        assert len(new_ast_body.items) == 3, ASTerr(new_ast_body)

        # Extract the preprocessing ASTs from the decoded skeleton file
        # ast.
        (pre_ast, main_ast, post_ast) = new_ast_body.items
        
        # return our decoded command block.  Each principal section is
        # processed synchronously within the command block.
        #res_ast = ASTNode('block_merge',
        res_ast = ASTNode('block',
                          ASTNode('sync', ASTNode('block', pre_ast)),
                          ASTNode('sync', ASTNode('block', main_ast)),
                          ASTNode('sync', ASTNode('block', post_ast))
                          )
        # Ugh..Because AST constructor was not designed to set name
        res_ast.name = '%s_%s_%s' % (obe_id.upper(), obe_mode.upper(),
                                     cmdname.upper())

        return res_ast
    
    
    def _decode_params(self, ast, eval):
        assert ast.tag == 'param_list', ASTerr(ast)

        res = Bunch.Bunch(caseless=True)
        
        # Iterate over subitems, each of which should be a var=exp pair.
        # Decode all value expressions and assign results to variables.
        for keyval in ast.items:
            assert keyval.tag == 'key_value_pair', ASTerr(keyval)

            (var, val_ast) = keyval.items
            assert type(var) == types.StringType, "variable is not a string"

            new_val_ast = self.decode(val_ast, eval)

            res[var] = new_val_ast

        return res

    def _decode_merge(self, body_ast, eval):

            new_ast = self.decode(body_ast, eval)
            
            # if result is a command list, then mark it for merging into
            # one large result
            if isinstance(new_ast, ASTNode) and \
                    new_ast.tag == 'cmdlist':
                new_ast = ASTNode('block_merge', *new_ast.items)

            return new_ast


def decode_abscmd(cmdstr, envstr, sk_bank, logger):

    import remoteObjects as ro
    ro.init()

    fakeStatus = {
        'STATL.TSC_F_SELECT': 'CS_IR',
        }
    
    # Create top level logger.
    logger = ssdlog.make_logger('sk_decode', options)

    sk_bank = skBank(options.skdir, logger=logger)

    variable_resolver = VariableResolver({})
    register_resolver = RegisterResolver()
    #status_resolver = MockStatusResolver(fakeStatus)
    status_resolver = StatusResolver(ro.remoteObjectProxy('status'))
    frame_source = MockFrameSource()

    eval = Evaluator(variable_resolver, register_resolver,
                     status_resolver, frame_source, logger)

    # Parse environment string into an AST, raising parse error if
    # necessary
    envstr = envstr.strip()
    if len(envstr) > 0:
        res = sk_bank.parser.parse_params(envstr)
        if res[0]:
            raise DecodeError("Error parsing default parameters '%s': %s" % (
                envstr, res[2]))

        try:
            ast_global_params = res[1]
            assert ast_global_params.tag == 'param_list', ASTerr(ast_global_params)

        except AssertionError, e:
            raise DecodeError("Malformed default parameter list '%s': AST=%s" % (envstr, str(ast_global_params)))

    else:
        ast_global_params = None

    # Set global env, if any
    if ast_global_params:
        eval.set_params(ast_global_params)

    # Parse command string into an AST, raising parse error if
    # necessary
    cmdstr = cmdstr.strip()
    res = sk_bank.parser.parse_opecmd(cmdstr)
    if res[0]:
        raise DecodeError("Error parsing command '%s': %s" % (
            cmdstr, res[2]))

    ast = res[1]
    assert ast.tag == 'cmdlist', ASTerr(ast)

    ast = ast.items[0]
    assert ast.tag == 'abscmd', ASTerr(ast)
    assert len(ast.items) == 2, ASTerr(ast)

    (ast_cmd_exp, ast_params) = ast.items

    # Make a *SUB ast and decode it
    ast = ASTNode('star_sub', ast_cmd_exp, ast_params)
    
    decoder = Decoder(eval, sk_bank, logger)

    newast = decoder.decode(ast, eval)

    print newast.AST2str()

    if options.verbose:
        print newast.printAST()

    return 0


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('sk_decode', options)

    if options.cmdstr:
        sk_bank = skBank(options.skdir, logger=logger)
        decode_abscmd(options.cmdstr, options.envstr, sk_bank, logger)
        sys.exit(0)
    
    if len(args) > 0:
        for filename in args:
            try:
                in_f = open(filename, 'r')
                buf = in_f.read()
                in_f.close()
            except IOError, e:
                print "Error opening file '%s'" % filename
                sys.exit(1)

            interp(options, filename, buf)

    else:
        buf = sys.stdin.read()
        interp(options, '<stdin>', buf)


if __name__ == "__main__":
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] "
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--cmd", dest="cmdstr",
                      help="The abstract command string to be decoded")
    optprs.add_option("--env", dest="envstr", default='',
                      help="The abstract command environment string")
    optprs.add_option("--action", dest="action",
                      help="decode")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--skdir", dest="skdir", default=obshome,
                      help="Base directory of the skeleton files")
    optprs.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Turn on verbose output")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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
