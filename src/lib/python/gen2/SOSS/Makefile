#
# Makefile for SOSS modules
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed May  8 15:43:55 HST 2013
#]
# Bruce Bon     2008-09-10
#

SUBDIRS = \
	DAQtk \
	frame \
	parse \
	INSint \
	TCSint \
	SOSSrpc \
	STARSint \
        DotParaFiles \
	status
#	GuiderInt \

.PHONY: subdirs $(SUBDIRS) all clean test

all: Makefile subdirs

clean: Makefile subdirs
	-rm -f *.pyc *.pyo *~ *.BAK

test: Makefile subdirs

testfunc:
	@echo 'testfunc: NOP'

doc: Makefile subdirs

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

#END Makefile
