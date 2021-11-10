#
# Makefile for the astro directory
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  last edit: 2007-08-30
#

TESTABLE_PYTHON_FILES =  fitsutils.py

NONTESTABLE_PYTHON_FILES = radec.py subaru.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
						$(NONTESTABLE_PYTHON_FILES)

DOC_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES)

PYDOC_FILES := $(DOC_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test doc

default: Makefile $(ALL_PYTHON_FILES)
	@echo 'default:'

all:    default doc
	@echo 'all:'

doc: default $(PYDOC_FILES)
	@echo 'doc:'
	-rm -f *.pyc

RUBBISH = *.pyc *.pyo *~ *.BAK *.log

clean: Makefile cleandoc
	@echo 'clean:'
	-rm -f $(RUBBISH) $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

cleandoc: Makefile
	@echo 'cleandoc:'
	rm -f $(PYDOC_FILES)

cleanall: Makefile clean cleandoc
	@echo 'cleanall:'
	-rm -f *.log

testunit: default
	@echo 'testunit:'
	# somehow pydoc makes a bad .pyc file, so remove before testing
	-rm -f *.pyc
	../test_all.py $(TEST_PY_FILES)

testfunc:
	@echo 'testfunc: NOP'

testcover: default
	@echo 'testcover:'
	../coverage.py -e

	@for f in $(TEST_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  ../coverage.py -x $$f; \
	done

	@for f in $(TESTABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ../coverage.py -a $$f; \
	done

	../coverage.py -r $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)


# testfunc: default
# 	@echo 'testfunc:'
# 	../test_all.py $(TESTFUNC_PY_FILES)

# test: testunit testfunc
test: testunit
	@echo 'test:'

testall: test testcover
	@echo 'testall:'

$(PYDOC_FILES): %.html : %.py
	pydoc.py -w `basename "$@" .html`

#END Makefile
