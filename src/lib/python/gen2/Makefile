#
# Makefile for /lib/
#
# Eric Jeschke (eric@naoj.org) 2010.02.20
# Bruce Bon     2007-09-04
#

SUBDIRS = \
	SOSS \
	astro \
	remoteObjects \
	Gen2

TESTABLE_PYTHON_FILES =  \
	StatusBundle.py \
	environment.py

NONTESTABLE_PYTHON_FILES =  \
	Bunch.py  \
	Monitor.py  \
	Task.py  \
	coverage.py  \
	lex.py  \
	myGetopt.py  \
	myproc.py  \
	pyfits.py  \
	rpc.py  \
	rpcgen.py  \
	test_all.py  \
	xdrlib.py  \
	yacc.py \
	ssdlog.py

CIAX_FILES = \
	Bunch.py \
	Monitor.py \
	NestedBunch.py \
	NestedException.py \
	Task.py \
	lex.py \
	myproc.py \
	ssdlog.py \
	yacc.py \
	rpc.py \
	xdrlib.py \
	rpcgen.py \
	remoteObjects \
	PubSub.py \
	SOSS/DotParaFiles \
	SOSS/INSint \
	SOSS/SOSSrpc \
	SOSS/TCSint \
	SOSS/status \
	SOSS/SkPara/cmd/TSC \
	SOSS/SkPara/cmd/OBS \
	SOSS/__init__.py \
	Gen2/__init__.py \
	Gen2/g2config.py \
	Gen2/BootManager.py \
	Gen2/TaskManager.py \
	Gen2/Tasks/g2Task.py \
	Gen2/Tasks/TCSdd.py \
	Gen2/Tasks/OBSdd.py \
	Gen2/Tasks/skTask.py \
	Gen2/client/g2cmd.py \
	cfg/g2soss.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

#? TESTFUNC_PY_FILES = testfunc_TASK.py
TESTFUNC_PY_FILES =  \
	test_Task.py

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
		    $(TESTFUNC_PY_FILES) $(NONTESTABLE_PYTHON_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

RUBBISH = *.pyc *.pyo *~ parser.out parsetab.py

.PHONY: subdirs $(SUBDIRS) all clean test

default:  Makefile subdirs

all: default

doc: $(PYDOC_FILES) subdirs

clean: Makefile subdirs cleanfiles

cleanfiles:
	-rm -f $(RUBBISH) $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

export_ro:
	tar czf ro.tgz --exclude=.svn Bunch.py myproc.py ssdlog.py \
	remoteObjects

export_roplus:
	tar czf ro+.tgz --exclude=.svn Bunch.py Monitor.py PubSub.py \
	myproc.py cgisrv.py remoteObjects ssdlog.py Task.py 

export_ciax:
	tar czf ciax.tgz --exclude=.svn $(CIAX_FILES)

export_simcam:
	tar czf simcam.tgz --exclude=.svn Bunch.py myproc.py ssdlog.py \
	remoteObjects StatusBundle.py Task.py SOSS/SOSSrpc SOSS/DAQtk \
	SOSS/INSint SOSS/DotParaFiles SOSS/SkPara SOSS/status SOSS/frame

test: default subdirs testunit testfunc

testunit: default
	@echo
	@echo 'testunit: $(TEST_PY_FILES)'
	./test_all.py  $(TEST_PY_FILES)

testfunc: default
	@echo
	@echo 'testfunc: $(TESTFUNC_PY_FILES)'
	./test_all.py  $(TESTFUNC_PY_FILES)

testcover:
	@echo 'testcover:'
	./coverage.py -e

	@for f in $(TEST_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  ./coverage.py -x $$f; \
	done

	@for f in $(TESTABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ./coverage.py -a $$f; \
	done

	./coverage.py -r $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
