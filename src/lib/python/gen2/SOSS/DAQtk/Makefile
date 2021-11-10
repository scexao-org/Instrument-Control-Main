#
# Makefile for SOSS.DAQtk module
#
# Eric Jeschke  2005.12.06
# Bruce Bon     2007-06-01
#

RUBBISH = *.pyc *.pyo *~ parser.out parsetab.py

TESTABLE_PYTHON_FILES = DAQtk.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)
NONTESTABLE_PYTHON_FILES = 

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py) \
                      $(NONTESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(RPCINT) $(TESTABLE_PYTHON_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test

default: $(ALL_PYTHON_FILES)

all: default doc

doc: $(PYDOC_FILES)

test: default
	../../test_all.py $(TEST_PY_FILES)

testall: test testcover

testcover: default
	@echo 'testcover:'
	../../coverage.py -e

	@for f in $(TEST_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  ../../coverage.py -x $$f; \
	done

	@for f in $(NONTESTABLE_PYTHON_FILES) $(TESTABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ../../coverage.py -a $$f; \
	done

	../../coverage.py -r $(NONTESTABLE_PYTHON_FILES) $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES)
	-rm -f $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
