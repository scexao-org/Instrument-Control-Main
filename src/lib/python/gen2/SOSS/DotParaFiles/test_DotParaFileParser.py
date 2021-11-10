#!/usr/bin/env python
# test_DotParaFileParser.py

import unittest, sys
import logging
import re

import SOSS.parse.para_lexer as para_lexer
from SOSS.parse.para_parser import NOP, paraParser
from DotParaFileParser import ParameterValidationException, \
     ParameterHandler, InconsistentParameterDefinitionException, \
     DotParaFileException

logger = logging.getLogger('para.test')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Parameter definition with case and NOP
test_str1 = '''
MOTOR \
    TYPE       = CHAR \
    DEFAULT    = ON \
    SET        = ON, SETUP, OFF 

F_SELECT \
    TYPE       = CHAR \
    DEFAULT    = NOP \
    SET        = P_OPT,P_IR,CS,CS_OPT,CS_IR,NS_OPT,NS_IR,NS_IR_OPTM2 \
    NOP        = NOP

COORD \
    TYPE       = CHAR \
    DEFAULT    = ABS \
    SET        = ABS,REL,OTHER

POSITION CASE=(COORD=ABS) \
    TYPE      = NUMBER \
    DEFAULT   = NOP \
    MIN       = -150.000 \
    MAX       = +150.000 \
    FORMAT    = %+08.3f \
    NOP       = NOP

POSITION \
    TYPE      = NUMBER \
    DEFAULT   = 0 \
    MIN       = -300.000 \
    MAX       = +300.000 \
    FORMAT    = %+08.3f

FOO CASE=(COORD=ABS) \
    TYPE      = NUMBER \
    DEFAULT   = @STATUS \
    MIN       = -200\
    MAX       = 200 \
    FORMAT    = %+08.3f \
    STATUS    = !TSCL.BAR

FOO CASE=(COORD=OTHER, F_SELECT=P_IR) \
    TYPE      = NUMBER \
    DEFAULT   = @STATUS \
    MIN       = -500\
    MAX       = 500 \
    FORMAT    = %+09.3f \
    STATUS    = !TSCL.FOO

FOO  \
    TYPE      = NUMBER \
    DEFAULT   = @SYSTEM \
    MIN       = -200 \
    MAX       = 200 \
    FORMAT    = %+08.3f
    
'''

class ParameterHandlerValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.lexer = para_lexer.paraScanner(logger=logger, debug=0)
        self.parser = paraParser(self.lexer, logger=logger, debug=0)

        self.paramObj = self.parser.parse_buf(test_str1)
        self.validator = ParameterHandler(self.paramObj)
        
    def testNopRejected(self):
        try:
            result = self.validator.validate({'POSITION': 'NOP', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'REL'})
            fail('The NOP parameter is for Position is notdefined and should have thrown exception')
        except ParameterValidationException, e:
            logger.debug(`e`)
            logger.debug(e.formatStackTrace())
        
    def testNopAccepted(self):
        result = self.validator.validate({'POSITION': 'NOP', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'ABS'})
        self.assertEqual(True, result)

    def testValueAccepted(self):
        result = self.validator.validate({'POSITION': '0', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'REL'})
        self.assertEqual(True, result)

    def testValueRejected(self):
        try:
            result = self.validator.validate({'POSITION': '400', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'REL'})
            fail('The value for Position is out of range and should have thrown exception')
        except ParameterValidationException, e:
            logger.debug(`e`)
            logger.debug(e.formatStackTrace())
            pass

#    def testPythonNoneAccepted(self):
#        result = self.validator.validate({'POSITION': None, 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'ABS'})
#        self.assertEqual(True, result)
#
#    def testPythonNoneRejected(self):
#        try:
#            result = self.validator.validate({'POSITION': None, 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'REL'})
#            fail('The NOP parameter is for Position is notdefined and should have thrown exception')
#        except ParameterValidationException, e:
#            logger.debug(`e`)
#            logger.debug(e.formatStackTrace())
#            pass

    def testPythonValueAccepted(self):
        result = self.validator.validate({'POSITION': 150, 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'ABS'})
        self.assertEqual(True, result)

    def testPythonValueRejected(self):
        try:
            result = self.validator.validate({'POSITION': 151, 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'ABS'})
            fail('The value for Position is out of range and should have thrown exception')
        except ParameterValidationException, e:
            logger.debug(`e`)
            logger.debug(e.formatStackTrace())
            pass

class ParameterHandlerPopulateTestCase(unittest.TestCase):
    def setUp(self):
        self.lexer = para_lexer.paraScanner(logger=logger, debug=0)
        self.parser = paraParser(self.lexer, logger=logger, debug=0)

        self.paramObj = self.parser.parse_buf(test_str1)
        self.validator = ParameterHandler(self.paramObj)
        
    def testPopulateWithNOP1(self):
        try:
            '''
            POSITION=NOP is not allowed here
            '''
            result = self.validator.populate({'POSITION':'NOP', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'REL', 'FOO':'5.0' })
            self.fail("should not reach here")
        except InconsistentParameterDefinitionException, e:
            logger.debug(str(e))
            logger.debug(e.formatStackTrace())
        except Exception, e:
            if issubclass(e.__class__, DotParaFileException):
                logger.error('HELLO')
                logger.error(e.formatStackTrace())
            self.fail("caught unexpected type of exception [%s] with message [%s]"% (e.__class__, e))
        
    def testPopulateWithNOP2(self):
        result = self.validator.populate({'POSITION':'NOP', 'MOTOR': 'ON', 'F_SELECT': 'NS_IR', 'COORD': 'ABS', 'FOO':'5.0'})
        self.assertEquals(NOP, result['POSITION'])
        
    def testPopulateWithDefaultValue(self):
        result = self.validator.populate({'POSITION':'NOP',  'F_SELECT': 'NS_IR', 'COORD': 'ABS', 'FOO':'5.0'})
        self.assertEquals('ON', result['MOTOR'])
        
    def testPopulateWithDefaultValueForNOP(self):
        '''
        F_SELECT has DEFAULT=NOP and NOP=NOP, so without specifying the value
        the defualt should result to NOP
        '''
        result = self.validator.populate({'POSITION':'NOP',  'COORD': 'ABS', 'FOO':'5.0'})
        self.assertEquals(NOP, result['F_SELECT'])
        
    def testPopulateWithDefaultValueForStatus(self):
        result = self.validator.populate({'POSITION':'NOP',  'COORD': 'ABS'}, statusMap = {'TSCL.BAR':'150'})
        self.assertEquals(150.0, result['FOO'])
        
    def testPopulateWithDefaultValueForRegister(self):
        result = self.validator.populate({'POSITION':'+100',  'COORD': 'REL'}, systemRegMap = {'FOO':120})
        logger.debug("after populating values %s" % str(result))
        self.assertEquals(120.0, result['FOO'])
 

class FuncRefTestCase(unittest.TestCase):
    funcref_sample = """
NAME TYPE=CHAR DEFAULT="test"
EXP TYPE=NUMBER DEFAULT=1 FORMAT=%.1f
OW TYPE=CHAR DEFAULT="N"
OBJECT TYPE=CHAR DEFAULT="#"
TYP TYPE=CHAR DEFAULT="OBJECT"
BIN TYPE=NUMBER DEFAULT=1 FORMAT=%d
FRAME0 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME1 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME2 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME3 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME4 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME5 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME6 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME7 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME8 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
FRAME9 TYPE=CHAR DEFAULT=&GET_F_NO[SPCAM A] NOP=NOP
"""
    def testFuncRef(self):
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(FuncRefTestCase.funcref_sample)
        paramDefs = paramObj.paramDict
        f1 = paramDefs['FRAME1'].getParamDefForParamMap()
        self.assertEquals('&GET_F_NO[SPCAM A]', f1['DEFAULT'])
        self.assertEquals('NOP', f1['NOP'])
 
class TestParaFileParse(unittest.TestCase):
    def testParse(self):
        t_str = 'DUMMY TYPE=CHAR SET=DUMMY DEFAULT=DUMMY\n'
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict

class TestNumericFormatString(unittest.TestCase):
    def testParse1(self):
        t_str = '''GAIN TYPE=NUMBER FORMAT=%ld DEFAULT=-7 NOP=NOP\n'''
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict
        ex = paramDefs['GAIN']
        self.assertEqual('%ld', ex.getParamDefForParamMap()['FORMAT'])
        
    def testParse2(self):
        t_str = '''BINMODE TYPE=NUMBER FORMAT=%-5.5d  MIN=-10  DEFAULT=9 NOP=NOP\n'''
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict
        ex = paramDefs['BINMODE']
        self.assertEqual('%-5.5d', ex.getParamDefForParamMap()['FORMAT'])
        
    def testParse3(self):
        t_str = '''PARTMODE TYPE=NUMBER FORMAT=%8.10f DEFAULT=-8 NOP=NOP\n'''
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict
        ex = paramDefs['PARTMODE']
        self.assertEqual('%8.10f', ex.getParamDefForParamMap()['FORMAT'])
        
class QuatedListTestCase(unittest.TestCase):
    t_str = '''
        SELECT   \
        TYPE=CHAR \
        DEFAULT=NOP \
        SET="open","ND","Grism","CH4s","CH4l","BrG","H2V10","Kcont","H2V21","COV20","HOME" \
        NOP=NOP
    '''
    def testParse(self):
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(QuatedListTestCase.t_str)
        paramDefs = paramObj.paramDict
        ex = paramDefs['SELECT']
        logger.debug(`ex.getParamDefForParamMap()['SET']`)

        self.assertEqual('NOP', ex.getParamDefForParamMap()['DEFAULT'])
        self.assertEqual('NOP', ex.getParamDefForParamMap()['NOP'])

class NOPTestCase(unittest.TestCase):
    def testParse1(self):
        t_str = '''
        UNIT   TYPE=CHAR DEFAULT=NOP NOP=NOP SET=ALL,CAMVME,SPGVME,UNA3,TC1,TC2,TC3,UNA7,ARYELEC,TM1,TM2,CAM_MTR,SPG_MTR,VAC1,UTSTRIP,UNB8
        CMD    TYPE=CHAR DEFAULT=NOP NOP=NOP SET=ON,OFF,STATUS
        '''
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict
        logger.debug(`paramDefs`)
        ex = paramDefs['UNIT']
        self.assertEqual('NOP', ex.getParamDefForParamMap()['DEFAULT'])
        self.assertEqual('NOP', ex.getParamDefForParamMap()['NOP'])

        ex = paramDefs['CMD']
        self.assertEqual('NOP', ex.getParamDefForParamMap()['DEFAULT'])
        self.assertEqual('NOP', ex.getParamDefForParamMap()['NOP'])

    def testParse2(self):
        # NOP in the SET should have been deleted
        t_str = '''
        UNIT   TYPE=CHAR DEFAULT=NOP NOP=NOP SET=ALL,CAMVME,SPGVME,UNA3,TC1,TC2,TC3,UNA7,ARYELEC,TM1,TM2,CAM_MTR,SPG_MTR,VAC1,UTSTRIP,UNB8,NOP
        '''
        lexer = para_lexer.paraScanner(logger=logger, debug=0)
        parser = paraParser(lexer, logger=logger, debug=0)

        paramObj = parser.parse_buf(t_str)
        paramDefs = paramObj.paramDict
        logger.debug(`paramDefs`)
        ex = paramDefs['UNIT']
        self.assertEqual('NOP', ex.getParamDefForParamMap()['DEFAULT'])
        self.assertEqual('NOP', ex.getParamDefForParamMap()['NOP'])
        self.assert_(not (ex.getParamDefForParamMap()['SET']).__contains__('NOP'))

class DomainExceptionsTestCase(unittest.TestCase):
    def testInconsistentParameterDefinitionException(self):
        def inner():
            try:
                raise InconsistentParameterDefinitionException(exception = Exception("hello"),
                                                             message = "something happened",
                                                             offendingKey = 'ME',
                                                             offendingAttributes = ['DEFAULT', 'NOP'])
            except DotParaFileException, e:
                raise ParameterValidationException(exception = e,
                                                   message = "something else happened",
                                                   offendingKey = 'YOU',
                                                   offendingValue = 2000)
        try:
            inner()
        except DotParaFileException, e:       
            lines = str(e).split('\n')
            self.assert_(re.match(r'(\w+\s*:\s*)?something else happened',  lines[0]))
            self.assert_(re.match(r'(\w+\s*:\s*)?something happened',  lines[1]))
            self.assert_(re.match(r'(\w+\s*:\s*)?hello',  lines[2]))

if __name__ == '__main__':
    unittest.main()
