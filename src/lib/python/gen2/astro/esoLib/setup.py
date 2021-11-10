"""
Distutils script for iqe_wrapper.

Yasuhiko Sakakibara - yasu@subaru.naoj.org
Eric Jeschke - eric@naoj.org
"""
import numpy
from distutils.core import setup, Extension
import sys

if not hasattr(sys, 'version_info') or sys.version_info < (2,2,0,'alpha',0):
     raise SystemExit, "Python 2.2 or later required to build this module."

incs = ["./"]
incs.append(numpy.get_numarray_include())
extension = Extension("iqe",
                      ['iqefunc.c',
                       'indexx.c',
                       'mrqfit.c',
                       'gaussj.c',
                       'covsrt.c',
                       'sort.c',
                       'iqe_wrapper.c'
                       ],
                      include_dirs=incs,
                      library_dirs=["./"],
                      libraries   =['m'])
     
setup(name     = "iqe",
   version     = "0.2",
   description = "A python wrapper for the eso librtd library functions.",
   packages    = [""],
   package_dir = {"":""},
   ext_modules = [extension])

