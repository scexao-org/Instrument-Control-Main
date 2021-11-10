#
# Makefile for Gen2/src directory
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Aug 27 14:12:32 HST 2007
#]
# Bruce Bon     2007-10-03
#

TESTABLE_PYTHON_FILES =  

NONTESTABLE_PYTHON_FILES =  \
		TaskManager.py \
		SessionManager.py \
		BootManager.py \
		frameSvc.py \
		g2config.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

TESTFUNCABLE_PYTHON_FILES = \
		TaskManager.py

NON_TESTFUNC_PY_FILES = 


TESTFUNC_PY_FILES := $(TESTFUNCABLE_PYTHON_FILES:%.py=testfunc_%.py)


ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py) \
		      $(TESTFUNC_PY_FILES:%.py=cover_%.py) \
		      $(TESTFUNCABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
		    $(TESTFUNC_PY_FILES) $(NONTESTABLE_PYTHON_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

SUBDIRS = Tasks


#export PYTHONPATH = $(PWD):$(PWD)/..

.PHONY: subdirs $(SUBDIRS) all default clean cleanall cleandoc test testall \
	testunit testfunc checkup update 

default: Makefile $(ALL_PYTHON_FILES)

all: default doc subdirs

doc: $(PYDOC_FILES) subdirs

clean: Makefile subdirs
	rm -f *.pyc $(PYDOC_FILES) $(ANNOTATED_PY_FILES) .coverage
	rm -f testfunc_TaskManager.png

cleanall: Makefile clean cleandoc subdirs
	rm -f *.log

cleandoc: Makefile subdirs
	rm -f $(PYDOC_FILES)

depgraph: $(ALL_PYTHON_FILES)
	PYTHONPATH=./:.. \
	  ../tools/py2depgraph.py testfunc_TaskManager.py | \
	     ../tools/depgraph2dot.py | \
	     dot -T png -o testfunc_TaskManager.png

test:  testunit testfunc subdirs
testall: test testcover subdirs

testunit: default subdirs
	PYTHONPATH=./:.. \
	   ../test_all.py $(TEST_PY_FILES)

testfunc: default subdirs
	PYTHONPATH=./:.. \
	   ../test_all.py $(TESTFUNC_PY_FILES)

TIMES_PER_SUITE = 10
SUITES_PER_EXEC = 2
teststress: default
	PYTHONPATH=./:.. \
	   ../test_all.py  --random --number=$(TIMES_PER_SUITE) \
	   --suites=$(SUITES_PER_EXEC) $(TEST_PY_FILES) $(TESTFUNC_PY_FILES)

#testenv: default

testcover: default
	@echo 'testcover:'
	PYTHONPATH=./:.. \
	   ../tools/coverage.py -e

	@for f in $(TEST_PY_FILES) $(TESTFUNC_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  PYTHONPATH=./:.. \
	     ../tools/coverage.py -x $$f; \
	done

	@for f in $(TESTABLE_PYTHON_FILES) $(TESTFUNCABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  PYTHONPATH=./:.. \
	     ../tools/coverage.py -a $$f; \
	done

	PYTHONPATH=./:.. \
	   ../tools/coverage.py -r $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
			      $(TESTFUNC_PY_FILES) $(NONTESTABLE_PYTHON_FILES)


checkup: update xupdate default xdefault xtest test

update:
	@echo updating ./
	svn up

$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=./:.. \
	   pydoc.py -w `basename "$@" .html`

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

#END
