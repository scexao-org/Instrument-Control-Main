#
# Makefile for FieldMonitor pycap module
# 
# Eric Jeschke  2010.08.14
#

# Location of python-dev include files
#PYTHON_INC=/usr/include/python2.4
PYTHON_INC=/usr/include/python2.6
# Location of numarray include files
#NUMARRAY_INC=/home/eric/Svn/lib/python/numarray-src/Include
NUMARRAY_INC=$(PYTHON_INC)/numarray

all:	pycap.so

pycap.so:	pycap.o
	gcc -shared -o pycap.so pycap.o

pycap.o:	pycap.c
	gcc -c -fPIC -I$(PYTHON_INC) -I$(NUMARRAY_INC) pycap.c

clean:
	-rm *.o *.so *.a cap *.pyc *.pyo *~

# END
