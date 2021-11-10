#
# Makefile for SOSS Instrument Interface module
#[ Eric Jeschke (eric@naoj.org) --
#]
#
# Bruce Bon     2007-06-01
#
RPCINT  = DAQtkDatSndMemconstants.py DAQtkDatSndMempacker.py \
	DAQtkDatSndMemtypes.py

GUI_FILES = GladeGen.py GladeGenConfig.py INSintGUI.py INSintTester.py

TESTFUNC_PY_FILES = testfunc_INSint.py

ALL_PYTHON_FILES := $(RPCINT) $(GUI_FILES) INSint.py \
			$(TESTFUNC_PY_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test doc

default: all

all: $(RPCINT) 

# TEMP: This is separated out for now because it doesn't build in buildbot
# Get a "RuntimeError: could not open display" when trying to import gtk
gui:	INSintTester

doc:	$(PYDOC_FILES)

INSintTester:   INSintGUI.py INSintTester.py

INSintGUI.py:   GladeGen.py INSintGUI.glade GladeGenConfig.py
	./GladeGen.py INSintGUI.glade INSintGUI INSintGUI
	-rm -f INSintGUI.pyc

testfunc: default
	@echo 'testfunc:'
	../../test_all.py $(TESTFUNC_PY_FILES)

test: default

testall: testfunc

depgraph: $(ALL_PYTHON_FILES)
	py2depgraph.py INSintTester.py | depgraph2dot.py | \
	      dot -T png -o dep-INSintTester.png
	py2depgraph.py INSint.py | depgraph2dot.py | \
	      dot -T png -o dep-INSint.png

$(RPCINT):      ../../rpcgen.py DAQtkDatSndMem.x
	# Don't regenerate files, because we had to customize the unpacker for IRCS,
	# which sends a non-standard (buggy?) packet
	#../../rpcgen.py DAQtkDatSndMem.x
	@echo "Nothing to do!"

RUBBISH = *.pyc *.pyo *~ parser.out dotParaParseY.* \
	parsetab.* INSintGUI.py dep-*.png

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES)

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
