#
# Makefile for STARS Interface module
#
#[ Eric Jeschke (eric@naoj.org) --
#]
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  last edit: 2007-06-01
#

RPC_X_FILES = DAQobcSndStartRcv.x DAQobcSndEndRcv.x

RPC_GEN_FILES := $(RPC_X_FILES:%.x=%constants.py) \
		 $(RPC_X_FILES:%.x=%packer.py) \
		 $(RPC_X_FILES:%.x=%types.py) \
		 parsetab.py

TESTABLE_PYTHON_FILES =  

NONTESTABLE_PYTHON_FILES =  $(RPC_GEN_FILES) \
	STARSint.py MakeIndexFile.py STARSintTester.py STARSintGUI.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

TESTFUNC_PY_FILES = testfunc_STARSint.py

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
			$(TESTFUNC_PY_FILES) $(NONTESTABLE_PYTHON_FILES)

DOC_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
	$(TESTFUNC_PY_FILES) STARSint.py MakeIndexFile.py STARSintTester.py

PYDOC_FILES := $(DOC_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test doc

default: Makefile $(ALL_PYTHON_FILES) 

all:    default doc

# TEMP: This is separated out for now because it doesn't build in buildbot
# Get a "RuntimeError: could not open display" when trying to import gtk
gui:	STARSintTester

doc: $(RPC_GEN_FILES) STARSintGUI.py $(PYDOC_FILES)
	@echo 'doc:'
	-rm -f *.pyc

RUBBISH	= $(PYDOC_FILES) $(RPC_GEN_FILES) *.pyc *.pyo *~ *.BAK parser.out \
	parsetab.py STARSintGUI.py STARSintGUI.glade*.bak STARSintGUI.gladep STARSint.db

clean: Makefile cleandoc
	@echo 'clean:'
	-rm -f $(RUBBISH)

cleandoc: Makefile
	@echo 'cleandoc:'
	-rm -f $(PYDOC_FILES)

cleanall: Makefile clean cleandoc
	@echo 'cleanall:'
	-rm -f *.log

testunit: default
	@echo 'testunit:'
	../../test_all.py $(TEST_PY_FILES)

testfunc: default
	@echo 'testfunc:'
	../../test_all.py $(TESTFUNC_PY_FILES)

test: testunit

testall: testunit testfunc


STARSintTester: STARSintGUI.py STARSintTester.py STARSint.py

STARSintGUI.py: GladeGen.py STARSintGUI.glade GladeGenConfig.py
	./GladeGen.py STARSintGUI.glade STARSintGUI STARSintGUI
	-rm -f STARSintGUI.pyc


$(RPC_GEN_FILES):  ../../rpcgen.py $(RPC_X_FILES)
	../../rpcgen.py DAQobcSndStartRcv.x
	../../rpcgen.py DAQobcSndEndRcv.x

# Added a PYTHONPATH so the rpc gen files will build html properly - yuck
$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=../../ pydoc.py -w `basename "$@" .html`

#END Makefile
