#
# Makefile for SOSS frame module
# eric@naoj.org
#
# Bruce Bon     2007-06-01
#
RPCINT  = OSSS_Frameconstants.py OSSS_Framepacker.py OSSS_Frametypes.py

ALL_PYTHON_FILES := $(RPCINT) SOSS_frame.py getFrame.py

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)


.PHONY: default all clean test

default: all

all:    $(RPCINT)

doc: $(PYDOC_FILES)

test: default

$(RPCINT):      ../../rpcgen.py OSSS_Frame.x
	../../rpcgen.py OSSS_Frame.x


RUBBISH = $(RPCINT) *.pyc *.pyo *~ parser.out parsetab.py

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES)

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
