#
# Makefile for SOSS infrastructure prototype
#
# Bruce Bon     2007-06-01
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Aug 25 10:03:34 HST 2006
#]
#

TESTFUNC_PY_FILES =  \
       testfunc_RemoteObjects.py

PYDOCABLE_PYTHON_FILES = \
       remoteObjectManagerSvc.py \
       remoteObjectNameSvc.py \
       remoteObjects.py

#       client_example.py
#       ro_example.py

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(PYDOCABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTFUNC_PYTHON_FILES) $(PYDOCABLE_PYTHON_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

.PHONY: default all test doc

default: $(ALL_PYTHON_FILES)

all: default doc

testfunc: default
	@echo 'testfunc:'
	../test_all.py $(TESTFUNC_PY_FILES)

testcover: default
	@echo 'testcover:'
	../coverage.py -e

	@for f in $(TESTFUNC_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  ../coverage.py -x $$f; \
	done

	@for f in $(PYDOCABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ../coverage.py -a $$f; \
	done

	../coverage.py -r $(PYDOCABLE_PYTHON_FILES) $(TESTFUNC_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)

test: #was testfunc

testall: test testcover

doc: $(PYDOC_FILES)

RUBBISH = *.pyc *.pyo *~ parser.out parsetab.py *.gladep *.log

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES)
	-rm -f $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
