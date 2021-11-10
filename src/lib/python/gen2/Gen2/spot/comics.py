import csv
import StringIO
import tempfile
import popen2
import os
import pexpect

import plan


class RecordSet(object):
    """Wrapper for tabular data."""

    def __init__(self, tableData, columnNames):
        self.data = tableData
        self.columns = columnNames
        self.columnMap = {}
        for name,n in zip(columnNames, xrange(10000)):
            self.columnMap[name] = n
        
    def __getitem__(self, n):
        return Record(self.data[n], self.columnMap)

    def __setitem__(self, n, value):
        self.data[n] = value

    def __delitem__(self, n):
        del self.data[n]

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return '%s: %s' % (self.__class__, self.columns)


class Record(object):
    """Wrapper for data row. Provides access by
    column name as well as position."""

    def __init__(self, rowData, columnMap):
        self.__dict__['_data_'] = rowData
        self.__dict__['_map_'] = columnMap

    def __getattr__(self, name):
        return self._data_[self._map_[name]]

    def __setattr__(self, name, value):
        try:
            n = self._map_[name]
        except KeyError:
            self.__dict__[name] = value
        else:
            self._data_[n] = value

    def __getitem__(self, n):
        return self._data_[n]

    def __setitem__(self, n, value):
        self._data_[n] = value

    def __getslice__(self, i, j):
        return self._data_[i:j]

    def __setslice__(self, i, j, slice):
        self._data_[i:j] = slice

    def __len__(self):
        return len(self._data_)
        
    def __str__(self):
        return '%s: %s' % (self.__class__, repr(self._data_))
#


COMICS_MODE_STRS = ('IMG_N','IMG_Q','SPC_NL','SPC_NM','SPC_NM_FULL',
            'SPC_NH_Ar','SPC_NH_S','SPC_NH_Ne','SPC_QM','SPC_QM_FULL','SPC_QH')
CENTRAL_WAVELENGTH_STRS = (
                    "None", "None",  '10.3',  '10.3',  '10.3',
            '8.99',     '10.51',   '12.81',    '19.00', '19.00',      '19.00')
CENTRAL_WAVELENGTH = dict(zip(COMICS_MODE_STRS,CENTRAL_WAVELENGTH_STRS))


COMICS_MODE = dict(zip(COMICS_MODE_STRS,range(len(COMICS_MODE_STRS))))


img_filter_defs = ('ArIII', 'HOLE',
                  'N10.5', 'N11.7', 'N12.4', 'N8.8', 'N9.7',
                  'NeII', 'NeRef_TEST',
                  'Q17.7', 'Q18.8', 'Q20.5', 'Q24.5', 'Q24.5_TEST',
                  'SIV', 'UIR11.2', 'UIR8.6')

#img_filter_consts = [i.replace('.','_') for i in img_filter_defs]
IMG_FILTER = dict(zip(img_filter_defs,img_filter_defs))

exp_mode_strings = ('IMG','SVSPC')
EXP_MODE = dict(zip(exp_mode_strings,exp_mode_strings))

class Detector(RecordSet):
  detectorInfoFields = (
     "Mode",     "ImgFilter",   "ExpMode",  "det",  "dispDet","ChopF","MaxInteg",
                                                                          "TexpI","TexpS","TexpSFlat")
  detectorInfo = (
    ('IMG_N',       'N8.8',       'IMG',   '100000', '100000',  0.45,   100,   1.0,   0,    0),      
    ('IMG_N',       'N9.7',       'IMG',   '100000', '100000',  0.45,   100,   0.4,   0,    0),      
    ('IMG_N',       'N10.5',      'IMG',   '100000', '100000',  0.45,   100,   0.6,   0,    0),      
    ('IMG_N',       'N11.7',      'IMG',   '100000', '100000',  0.45,   100,   0.8,   0,    0),      
    ('IMG_N',       'N12.4',      'IMG',   '100000', '100000',  0.45,   100,   0.6,   0,    0),      
    ('IMG_N',       'UIR8.6',     'IMG',   '100000', '100000',  0.45,   100,   1.0,   0,    0),      
    ('IMG_N',       'UIR11.2',    'IMG',   '100000', '100000',  0.45,   100,   1.0,   0,    0),      
    ('IMG_N',       'ArIII',      'IMG',   '100000', '100000',  0.45,    45,   5.0,   0,    0),      
    ('IMG_N',       'SIV',        'IMG',   '100000', '100000',  0.45,   100,   4.0,   0,    0),      
    ('IMG_N',       'NeII',       'IMG',   '100000', '100000',  0.45,   100,   3.0,   0,    0),      
    ('IMG_N',       'NeRef_TEST', 'IMG',   '100000', '100000',  0.45,   100,   2.0,   0,    0),      

    ('SPC_NL',      'HOLE',       'SVSPC', '100110', '100100',  0.45,    45,   0.1,   3,    1),      
    ('SPC_NL',      'N8.8',       'SVSPC', '100110', '100100',  0.45,    45,   1.0,   3,    1),      
    ('SPC_NL',      'N9.7',       'SVSPC', '100110', '100100',  0.45,    45,   0.4,   3,    1),      
    ('SPC_NL',      'N10.5',      'SVSPC', '100110', '100100',  0.45,    45,   0.3,   3,    1),      
    ('SPC_NL',      'N11.7',      'SVSPC', '100110', '100100',  0.45,    45,   0.8,   3,    1),      
    ('SPC_NL',      'N12.4',      'SVSPC', '100110', '100100',  0.45,    45,   0.6,   3,    1),      

    ('SPC_NM',      'HOLE',       'SVSPC', '111111', '100100',  0.25,    25,   0.1,  16,   10),      
    ('SPC_NM',      'N8.8',       'SVSPC', '111111', '100100',  0.25,    25,   1.0,  16,   10),      
    ('SPC_NM',      'N9.7',       'SVSPC', '111111', '100100',  0.25,    25,   0.4,  16,   10),      
    ('SPC_NM',      'N10.5',      'SVSPC', '111111', '100100',  0.25,    25,   0.6,  16,   10),      
    ('SPC_NM',      'N11.7',      'SVSPC', '111111', '100100',  0.25,    25,   0.8,  16,   10),      
    ('SPC_NM',      'N12.4',      'SVSPC', '111111', '100100',  0.25,    25,   0.8,  16,   10),      

    ('SPC_NM_FULL', 'HOLE',       'SVSPC', '011101', '122222',  0.25,    20,   0.1,  16,   10),      
    ('SPC_NM_FULL', 'N8.8',       'SVSPC', '011101', '122222',  0.25,    20,   1.0,  16,   10),      
    ('SPC_NM_FULL', 'N9.7',       'SVSPC', '011101', '122222',  0.25,    20,   0.4,  16,   10),      
    ('SPC_NM_FULL', 'N10.5',      'SVSPC', '011101', '122222',  0.25,    20,   0.6,  16,   10),      
    ('SPC_NM_FULL', 'N11.7',      'SVSPC', '011101', '122222',  0.25,    20,   0.8,  16,   10),      
    ('SPC_NM_FULL', 'N12.4',      'SVSPC', '011101', '122222',  0.25,    20,   0.8,  16,   10),      

    ('SPC_NH_Ar',   'HOLE',       'SVSPC', '100101', '100100',  0.03,   150,   5.0, 100,   50),      
    ('SPC_NH_S',    'HOLE',       'SVSPC', '100101', '100100',  0.03,   150,   4.0, 100,   50),      
    ('SPC_NH_Ne',   'HOLE',       'SVSPC', '100101', '100100',  0.03,   150,   2.0, 100,   50),      

    ('IMG_Q',       'Q17.7',      'IMG',   '100000', '100000',  0.45,   100,   0.2,   0,    0),      
    ('IMG_Q',       'Q18.8',      'IMG',   '100000', '100000',  0.45,   100,   0.3,   0,    0),      
    ('IMG_Q',       'Q20.5',      'IMG',   '100000', '100000',  0.45,   100,   0.3,   0,    0),      
    ('IMG_Q',       'Q24.5',      'IMG',   '100000', '100000',  0.45,   100,   0.3,   0,    0),      
    ('IMG_Q',       'Q24.5_TEST', 'IMG',   '100000', '100000',  0.45,   100,   0.6,   0,    0),      

    ('SPC_QM',      'HOLE',       'SVSPC', '100101', '100100',  0.15,   120,   0.1,  12,    8),      
    ('SPC_QM',      'Q17.7',      'SVSPC', '100101', '100100',  0.15,   120,   0.2,  12,    8),      
    ('SPC_QM',      'Q18.8',      'SVSPC', '100101', '100100',  0.15,   120,   0.3,  12,    8),      
    ('SPC_QM',      'Q20.5',      'SVSPC', '100101', '100100',  0.15,   120,   1.0,  12,    8),      
    ('SPC_QM',      'Q24.5',      'SVSPC', '100101', '100100',  0.15,   120,   0.3,  12,    8),      
    ('SPC_QM',      'Q24.5_TEST', 'SVSPC', '100101', '100100',  0.15,   120,   0.3,  12,    8),      

    ('SPC_QM_FULL', 'HOLE',       'SVSPC', '111111', '122222',  0.15,    35,   0.1,  12,    8),      
    ('SPC_QM_FULL', 'Q17.7',      'SVSPC', '111111', '122222',  0.15,    35,   0.3,  12,    8),      
    ('SPC_QM_FULL', 'Q18.8',      'SVSPC', '111111', '122222',  0.15,    35,   0.5,  12,    8),      
    ('SPC_QM_FULL', 'Q20.5',      'SVSPC', '111111', '122222',  0.15,    35,   1.0,  12,    8),      
    ('SPC_QM_FULL', 'Q24.5',      'SVSPC', '111111', '122222',  0.15,    35,   0.3,  12,    8),      
    ('SPC_QM_FULL', 'Q24.5_TEST', 'SVSPC', '111111', '122222',  0.15,    35,   0.3,  12,    8),      

    ('SPC_QH',       'HOLE',      'SVSPC', '110100', '100100',  0.03,    60,   0.3, 100,   15),      

  )
  def __init__(self):
    super(Detector,self).__init__(Detector.detectorInfo,Detector.detectorInfoFields)
    self.mode_filter2row = {}
    for i,row in enumerate(self):
      self.mode_filter2row[(row.Mode,row.ImgFilter)] = self[i]
    #
  def getRowByModeFilter(self,mode,img_filter):
    return(self.mode_filter2row[(mode,img_filter)])
#

COMBO = {}
for mode in COMICS_MODE_STRS:
  COMBO[mode] = []
  for row in Detector.detectorInfo:
    if row[0] == mode:
      COMBO[mode].append(row[1])
    #
  #
#


img_filter_name_strings = (
'F05C08.70W0.80',
'F06C09.80W0.90',
'F07C10.30W1.05',
'F08C11.60W1.10',
'F09C12.50W1.15',
'F11C24.50W2.20',
'F32C13.10W0.20',
'F36C17.65W0.90',
'F37C18.75W0.85',
'F39C20.50W1.00',
'F42C24.50W0.80',
'H01')

IMG_FILTER_NAME = dict(zip(img_filter_name_strings,img_filter_name_strings))

pre_filter1_strings = (
'F01C10.50W6.00',
'F17C19.00W3.80',
'F26C10.52W0.16',
'F30C12.81W0.20',
'H13')

PRE_FILTER1 = dict(zip(pre_filter1_strings,pre_filter1_strings))

pre_filter2_strings = (
'F22C08.60W0.43',
'F23C08.99W0.13',
'F29C11.30W0.60',
'F34C17.00W0.40',
'H21')

PRE_FILTER2 = dict(zip(pre_filter2_strings,pre_filter2_strings))

grttype_strings = (
'G01L10L', 
'G02L10M',
'G03L10H',
'G04L20M',
'G04L20M',
'KEEP')

GRTTYPE = dict(zip(grttype_strings,grttype_strings))

class Optics(RecordSet):
  opticsInfoFields = (
    'Mode',        'ImgFilter',   'ImgFilterName',  'PreFilter1',      'PreFilter2',      'Lens', 'GrtType','GrtPosA',
                                                                                                              'GrtPosB',
                                                                                                                  'GrtPosWC',
                                                                                                                     'GrtPosScan'
  )

  opticsInfo = (
    ('IMG_N',       'N8.8',       'F05C08.70W0.80', 'F01C10.50W6.00',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'N9.7',       'F06C09.80W0.90', 'F01C10.50W6.00',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'N10.5',      'F07C10.30W1.05', 'F01C10.50W6.00',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'N11.7',      'F08C11.60W1.10', 'F01C10.50W6.00',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'N12.4',      'F09C12.50W1.15', 'F01C10.50W6.00',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'UIR8.6',     'H01',            'H13',             'F22C08.60W0.43', 'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'UIR11.2',    'H01',            'H13',             'F29C11.30W0.60', 'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'ArIII',      'H01',            'H13',             'F23C08.99W0.13', 'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'SIV',        'H01',            'F26C10.52W0.16',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'NeII',       'H01',            'F30C12.81W0.20',  'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),
    ('IMG_N',       'NeRef_TEST', 'F32C13.10W0.20', 'H13',             'H21',            'L01L10I',  'KEEP',    0, 0, 0, 'OFF'),

    ('SPC_NL',      'HOLE',       'H01',            'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),
    ('SPC_NL',      'N8.8',       'F05C08.70W0.80', 'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),
    ('SPC_NL',      'N9.7',       'F06C09.80W0.90', 'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),
    ('SPC_NL',      'N10.5',      'F07C10.30W1.05', 'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),
    ('SPC_NL',      'N11.7',      'F08C11.60W1.10', 'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),
    ('SPC_NL',      'N12.4',      'F09C12.50W1.15', 'F01C10.50W6.00',  'H21',            'L01L10I',  'G01L10L', 0, 0, 0, 'OFF'),

    ('SPC_NM',      'HOLE',       'H01',            'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 
    ('SPC_NM',      'N8.8',       'F05C08.70W0.80', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 
    ('SPC_NM',      'N9.7',       'F06C09.80W0.90', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 
    ('SPC_NM',      'N10.5',      'F07C10.30W1.05', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 
    ('SPC_NM',      'N11.7',      'F08C11.60W1.10', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 
    ('SPC_NM',      'N12.4',      'F09C12.50W1.15', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'OFF'), 

    ('SPC_NM_FULL', 'HOLE',       'H01',            'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  
    ('SPC_NM_FULL', 'N8.8',       'F05C08.70W0.80', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  
    ('SPC_NM_FULL', 'N9.7',       'F06C09.80W0.90', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  
    ('SPC_NM_FULL', 'N10.5',      'F07C10.30W1.05', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  
    ('SPC_NM_FULL', 'N11.7',      'F08C11.60W1.10', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  
    ('SPC_NM_FULL', 'N12.4',      'F09C12.50W1.15', 'F01C10.50W6.00',  'H21',            'L01L10I', 'G02L10M', 0, 0, 0, 'ON'),  

    ('SPC_NH_Ar',   'HOLE',       'H01',            'H13',             'F23C08.99W0.13', 'L01L10I', 'G03L10H', 0, 0, 0, 'OFF'), 
    ('SPC_NH_S',    'HOLE',       'H01',            'F26C10.52W0.16',  'H21',            'L01L10I', 'G03L10H', 0, 0, 0, 'OFF'), 
    ('SPC_NH_Ne',   'HOLE',       'H01',            'F30C12.81W0.20',  'H21',            'L01L10I', 'G03L10H', 0, 0, 0, 'OFF'), 

    ('IMG_Q',       'Q17.7',      'F36C17.65W0.90', 'H13',             'H21',            'L02L20I', 'KEEP',    0, 0, 0, 'OFF'), 
    ('IMG_Q',       'Q18.8',      'F37C18.75W0.85', 'F17C19.00W3.80',  'H21',            'L02L20I', 'KEEP',    0, 0, 0, 'OFF'), 
    ('IMG_Q',       'Q20.5',      'F39C20.50W1.00', 'H13',             'H21',            'L02L20I', 'KEEP',    0, 0, 0, 'OFF'), 
    ('IMG_Q',       'Q24.5',      'F11C24.50W2.20', 'H13',             'H21',            'L02L20I', 'KEEP',    0, 0, 0, 'OFF'), 
    ('IMG_Q',       'Q24.5_TEST', 'F42C24.50W0.80', 'H13',             'H21',            'L02L20I', 'KEEP',    0, 0, 0, 'OFF'), 

    ('SPC_QM',      'HOLE',       'H01',            'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 
    ('SPC_QM',      'Q17.7',      'F36C17.65W0.90', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 
    ('SPC_QM',      'Q18.8',      'F37C18.75W0.85', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 
    ('SPC_QM',      'Q20.5',      'F39C20.50W1.00', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 
    ('SPC_QM',      'Q24.5',      'F11C24.50W2.20', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 
    ('SPC_QM',      'Q24.5_TEST', 'F42C24.50W0.80', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'OFF'), 

    ('SPC_QM_FULL', 'HOLE',       'H01',            'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  
    ('SPC_QM_FULL', 'Q17.7',      'F36C17.65W0.90', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  
    ('SPC_QM_FULL', 'Q18.8',      'F37C18.75W0.85', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  
    ('SPC_QM_FULL', 'Q20.5',      'F39C20.50W1.00', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  
    ('SPC_QM_FULL', 'Q24.5',      'F11C24.50W2.20', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  
    ('SPC_QM_FULL', 'Q24.5_TEST', 'F42C24.50W0.80', 'F17C19.00W3.80',  'H21',            'L02L20I', 'G04L20M', 0, 0, 0, 'ON'),  

    ('SPC_QH',      'HOLE',       'H01',            'H13',             'F34C17.00W0.40', 'L02L20I', 'G03L10H', 0, 0, 0, 'OFF'), 
  )

  def __init__(self):
    super(Optics,self).__init__(Optics.opticsInfo,Optics.opticsInfoFields)

#

##### need to define the physical model also (e.g. pixels to arcsecs,
##### detector sizes and relations...


class Activity(object):
  INI_HEADER_STR = """# START 
#-------------------------------------------- 
# COMICS Observation Planning Applet          
# 
# %(timestamp)s
#-------------------------------------------- 
Version                = 0.1.4
#-------------------------------------------- 
# [Target Information] 
Target_Name            = %(Target_Name)s
Target_RA              = %(Target_RA)s
Target_Dec             = %(Target_Dec)s
Equinox                = %(Equinox)s
#-------------------------------------------- 
# [Telescope] 
Chopping_Throw         = %(Chopping_Throw)s
Chopping_PA            = %(Chopping_PA)s
Nod_Throw              = %(Nod_Throw)s
Nod_PA                 = %(Nod_PA)s
Inst_PA                = %(Inst_PA)s
Offset_X               = %(Offset_X)s
Offset_Y               = %(Offset_Y)s
Auto_Guide             = %(Auto_Guide)s
#-------------------------------------------- 
# [COMICS optics] 
COMICS_Mode            = %(COMICS_Mode)s
Imaging_Filter         = %(Imaging_Filter)s
Central_Wavelength     = %(Central_Wavelength)s
Slit_Width             = %(Slit_Width)s
#-------------------------------------------- 
# [Detector read out] 
Integration_Time_1beam = %(Integration_Time_1beam)s
Readout_Priority       = %(Readout_Priority)s
#-------------------------------------------- 
# [Reduction Recipe] 
Reduction_recipe       = %(Reduction_recipe)s
#-------------------------------------------- 
# [Observation Sequence] 
Position_adjust        = %(Position_adjust)s
Repeat                 = %(Repeat)s
%(Offsets)s#-------------------------------------------- 
# [Comments] 
#>  
#-------------------------------------------- 
# END 
"""

  STATUS_STRS = ("New", "Ready", "Made", "Done")
  STATUS = dict(zip(STATUS_STRS,range(len(STATUS_STRS))))
  DEF_STATUS = "New"

  OFFSET_RA_STR  = "Scan_Dra%02d             = %s\n"
  OFFSET_DEC_STR = "Scan_Ddec%02d            = %s\n"

  def __init__(self,target,telConfig,instConfig,dither,
               comment=None,status=None,tag=None):
    self.name = target.name  #+"_"+instConfig.name
    self.target = target
    self.telConfig = telConfig
    self.instConfig = instConfig
    self.dither = dither

    self.comment = comment
    if self.comment == None:
      self.comment = ""

    self.status = status
    if self.status == None:
      self.status = Activity.DEF_STATUS

    self.tag = tag
    if self.tag == None:
      self.tag = ""


  def SendOPEFile(self,outfilename,login,host,destname,passwd):
      #cmdline = "ssh -o ConnectTimeout=10 -l %s %s %s" % (login, host, subcmd)
      cmd = """scp %s %s@%s:./Procedure/%s""" % (
                                     outfilename,login,host,destname)
      print "Sending %s to %s as %s" % (outfilename,host,login)
      #logger.debug("Sending OPE: %s",cmd)
      try:
        child = pexpect.spawn(cmd)
        i = child.expect(['[Pp]assword:','continue connecting (yes/no)?'],timeout=10)
        if i == 1:
          #print child.before
          child.sendline('yes')
          child.expect('[Pp]assword:',timeout=10)
        child.sendline(passwd)
        child.expect(pexpect.EOF,timeout=10)
        #print child.before
        lines = child.before.split("\r\n")
        #print(lines)
        # first line is blank
        #print ">"+lines[0:1],"<"
        #print "[",lines[2:],"]"
        print child.before
        #print "+",host
      except KeyboardInterrupt, e:
        raise e
      except pexpect.TIMEOUT:
        print "scp timeout: %s@%s" % (login,host)
        #logger.error("SSH timeout: %s@%s",login,host)
      except Exception, e:
        pass
        print host
        print e
        #logger.exception("Exception taken for %s",host)
    #
  #



  def MakeOPEFile(self,outfile,timestamp,oAcct,passwd):
    outbase = os.path.basename(outfile.name)
    (outname,outext) = os.path.splitext(outbase)
    (inihandle, inifilename) = tempfile.mkstemp('.txt',outname+'_')
    self.MakeIniFile(open(inifilename,'w'),timestamp)
    cmd = "./app2ope.pl %s" % (inifilename)
    print cmd, ">",outfile.name
    (outlines,inlines,errlines) = popen2.popen3(cmd)
    outfile.write(outlines.read())
    outfile.close()
    print errlines.read()
    # commented out the os.remove() so they have a record of all the inifiles
    # os.remove(inifilename)
    if oAcct:
      if oAcct[0] == '-':
        host = 'localhost'
        oAcct = oAcct[1:]
      elif oAcct[0] == '+':
        host = 'mdbs1'
        oAcct = oAcct[1:]
      else:  # a test account
        host = 'dbs1'
      #
      self.SendOPEFile(outfile.name,oAcct,host,outbase,passwd)

  def MakeIniFile(self,outfile,timestamp):
    plan.Target.TARGET_EQUINOX[self.target.equinox]  # throw if bad equinox
    equinox = self.target.equinox[1:]
    
    chop_pa = self.telConfig.chop.pa
    if True == self.telConfig.chop.use_def_pa:
      chop_pa = 'default'
    #
    use_nodding = self.telConfig.use_nodding
    nod_throw = self.telConfig.nod.throw
    nod_pa = self.telConfig.nod.pa
    if False == use_nodding:
      nod_throw = 'not_used'
      nod_pa = 'not_used'
    elif True == self.telConfig.nod.use_def_pa:
      nod_pa = 'default'
    #
    autoguide = self.telConfig.use_autoguide
    if True == autoguide:
      autoguide = 'ON'
    else:
      autoguide = 'OFF'
    #
    center_wavelength = self.instConfig.center_wavelength
    if "None" == center_wavelength:
      center_wavelength = 'not_used'
    #
    slit_width = self.instConfig.slit_width
    if None == slit_width:
      slit_width = 'mirror'
    #
    pos_adjust = self.dither.pos_adjust
    if True == pos_adjust:
      pos_adjust = 'Enable'
    else:
      pos_adjust = 'Disable'
    #
    offsetsIniString = ""
    for (i, (ra_off,dec_off)) in enumerate(self.dither.offsets):
      offsetsIniString += self.OFFSET_RA_STR % (i+1,ra_off)
      offsetsIniString += self.OFFSET_DEC_STR % (i+1,dec_off)



    val_dict = {'timestamp': timestamp,
     'Target_Name': self.target.name, 'Target_RA': self.target.ra,
     'Target_Dec': self.target.dec,   'Equinox': equinox,
     'Chopping_Throw': self.telConfig.chop.throw,
     'Chopping_PA': chop_pa,
     'Nod_Throw': nod_throw,
     'Nod_PA': nod_pa,
     'Inst_PA': self.telConfig.inst_pa,
     'Offset_X': self.telConfig.offset[0],
     'Offset_Y': self.telConfig.offset[1],
     'Auto_Guide': autoguide,
     'COMICS_Mode': self.instConfig.mode,
     'Imaging_Filter': self.instConfig.img_filter,
     'Central_Wavelength': center_wavelength,
     'Slit_Width': slit_width,
     'Integration_Time_1beam': self.instConfig.integ_time_per_beam,
     'Readout_Priority': self.instConfig.readout_priority,
     'Reduction_recipe': self.target.style,
     'Position_adjust': pos_adjust,
     'Repeat' :self.dither.repeat,
     'Offsets' : offsetsIniString,
     }
    outfile.write(self.INI_HEADER_STR % val_dict)


class InstConfig(object):
  READOUT_PRIORITY_STRS = ("Partially_Readout","ND_READOUT")
  READOUT_PRIORITY = dict(zip(READOUT_PRIORITY_STRS,range(len(READOUT_PRIORITY_STRS))))

  SLIT_WIDTH_STRS = ("2", "3", "4", "mirror")
  SLIT_WIDTH = dict(zip(SLIT_WIDTH_STRS,range(len(SLIT_WIDTH_STRS))))

  DEF_COMICS_MODE = 'IMG_N'
  DEF_IMG_FILTER = None
  DEF_CENTER_WAVELENGTH = "None"
  DEF_SLIT_WIDTH = "mirror"
  DEF_INTEG_TIME_PER_BEAM = '100'
  DEF_READOUT_PRIORITY = 'Partially_Readout'
  def __init__(self,name=plan.UNTITLED,mode=DEF_COMICS_MODE,img_filter=DEF_IMG_FILTER,
                    center_wavelength=DEF_CENTER_WAVELENGTH,
                    slit_width=DEF_SLIT_WIDTH,
                    integ_time_per_beam=DEF_INTEG_TIME_PER_BEAM,
                    readout_priority=DEF_READOUT_PRIORITY):
    self.name = name
    self.mode = mode
    self.img_filter = img_filter
    if None == self.img_filter:
      self.img_filter = COMBO[self.mode][0]
    #

    self.center_wavelength = center_wavelength ## DEF_CENTER_WAVELENGTH,
    self.slit_width = slit_width ## DEF_SLIT_WIDTH,
    self.integ_time_per_beam = integ_time_per_beam ## DEF_INTEG_TIME_PER_BEAM,
    self.readout_priority = readout_priority ## DEF_READOUT_PRIORITY
  def __repr__(self):
    return("""comics.InstConfig(name=%r,
  mode=%r, img_filter=%r,
  center_wavelength=%r, slit_width=%r,
  integ_time_per_beam=%r, readout_priority=%r)""" % (
              self.name,self.mode,
              self.img_filter,
              self.center_wavelength,self.slit_width,
              self.integ_time_per_beam,self.readout_priority))

class Chop(object):
  DEF_THROW = '10.0'
  DEF_PA = '0.0'
  DEF_USE_DEF_PA = True
  def __init__(self,throw=DEF_THROW,use_def_pa=DEF_USE_DEF_PA,pa=DEF_PA):
    self.throw = throw
    self.use_def_pa = use_def_pa
    self.pa = pa
  def __repr__(self):
    return( "comics.Chop(throw=%r, use_def_pa=%r, pa=%r)" % (
             self.throw,self.use_def_pa,self.pa))

class Nod(Chop):
  DEF_THROW = '20.0'
  DEF_PA = '0.0'
  def __init__(self,throw=DEF_THROW,use_def_pa=True,
                                                                pa=DEF_PA):
    super(Nod,self).__init__(throw,use_def_pa,pa)
  def __repr__(self):
    return( "comics.Nod(throw=%r, use_def_pa=%r, pa=%r)" % (
             self.throw,self.use_def_pa,self.pa))

class TelConfig(object):
  DEF_USE_AUTOGUIDE = True
  DEF_OFFSET = ('-15.0','0.0')
  DEF_INST_PA = '0.0'
  DEF_USE_NODDING = True
  def __init__(self,name=plan.UNTITLED,chop=None,use_nodding=DEF_USE_NODDING,
                    nod=None,offset=None,
                    inst_pa=DEF_INST_PA,use_autoguide=DEF_USE_AUTOGUIDE):
    self.name = name
    self.chop = chop
    if self.chop == None:
      self.chop = Chop()
    self.use_nodding = use_nodding
    self.nod = nod
    if self.nod == None:
      self.nod = Nod()
    self.inst_pa = inst_pa
    self.offset = offset
    if self.offset == None:
      self.offset = list(TelConfig.DEF_OFFSET)
    self.use_autoguide = use_autoguide
  def __str__(self):
    return("%s(%s,%s,%s,%s,%s,%s)"%(self.name,self.chop,self.use_nodding,
           self.nod,self.inst_pa,self.offset,self.use_autoguide))
  def __repr__(self):
    return('''comics.TelConfig(name=%r,
  chop=%r,
  use_nodding=%r, nod=%r,
  inst_pa=%r, offset=%r, use_autoguide=%r)'''%(
             self.name,self.chop,self.use_nodding,
             self.nod,self.inst_pa,self.offset,self.use_autoguide))

class Dither(object):
  DEF_POS_ADJUST = True
  DEF_REPEAT = 1
  def __init__(self,name=plan.UNTITLED,pos_adjust=None,repeat=None,
               use_dithering=None,offsets=None):
    self.name = name
    self.pos_adjust = pos_adjust
    if self.pos_adjust == None:
      self.pos_adjust = Dither.DEF_POS_ADJUST
    self.repeat = repeat
    if self.repeat == None:
      self.repeat = Dither.DEF_REPEAT
    self.offsets = offsets
    if self.offsets == None:
      self.offsets = []
    self.use_dithering = use_dithering
    if self.use_dithering == None:
      self.use_dithering = False
  def __repr__(self):
    return("""comics.Dither(name=%r,
  pos_adjust=%r, repeat=%r, use_dithering=%r,
  offsets=%r)""" % (self.name,
       self.pos_adjust,self.repeat,self.use_dithering,self.offsets))


