#
# Makefile for SOSS.GuiderInt module
#
# Bruce Bon     2007-06-01


TESTABLE_PYTHON_FILES =  \
		guiderint.py

#NONTESTABLE_PYTHON_FILES =  \
#		$(RPC_GEN_FILES) TCStables.py STATintTester.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

#TESTFUNC_PY_FILES = testfunc_STATint.py testfunc_STATdecode.py


COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
			$(TESTFUNC_PY_FILES) $(NONTESTABLE_PYTHON_FILES)

DOC_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
			$(TESTFUNC_PY_FILES)

PYDOC_FILES := $(DOC_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test doc

default: Makefile $(ALL_PYTHON_FILES)

all:    default doc

doc: default $(PYDOC_FILES)
	@echo 'doc:'
	-rm -f *.pyc

RUBBISH = *.pyc *.pyo *~ *.BAK parser.out $(PYDOC_FILES) $(RPC_GEN_FILES)

clean: Makefile cleandoc
	@echo 'clean:'
	-rm -f $(RUBBISH) $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)


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

test: testunit testfunc

testall: testunit testfunc testcover

testcover: default
	@echo 'testcover:'
	../../coverage.py -e

	@for f in $(TEST_PY_FILES); do \
	  echo Checking coverage for $$f; \
	  ../../coverage.py -x $$f; \
	done

	@for f in $(TESTABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ../../coverage.py -a $$f; \
	done

	../../coverage.py -r $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)

# Added a PYTHONPATH so the rpc gen files will build html properly - yuck
$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=../../ pydoc.py -w `basename "$@" .html`

#END Makefile
