#
# Makefile for SOSS rpc module
# eric@naoj.org
#
# Bruce Bon     2007-06-01
#
RPC_GEN_FILES  = OSSC_ComCDconstants.py OSSC_ComCDpacker.py OSSC_ComCDtypes.py

TESTABLE_PYTHON_FILES =  \
	       SOSSrpc.py

NONTESTABLE_PYTHON_FILES =  \
	       $(RPC_GEN_FILES) parsetab.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

DOC_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(NONTESTABLE_PYTHON_FILES)

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
				$(NONTESTABLE_PYTHON_FILES)

PYDOC_FILES := $(DOC_PYTHON_FILES:%.py=%.html)

.PHONY: default all clean test

default: $(RPC_GEN_FILES)

all: default doc

doc: $(PYDOC_FILES)

$(RPC_GEN_FILES):      ../../rpcgen.py OSSC_ComCD.x
	../../rpcgen.py OSSC_ComCD.x

test: 
	../../test_all.py $(TEST_PY_FILES)

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


RUBBISH = *.pyc *.pyo *~ *.BAK parser.out parsetab.py

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES) $(RPC_GEN_FILES)
	-rm -f $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

# Added a PYTHONPATH so the rpc gen files will build html properly - yuck
$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=../../ pydoc.py -w `basename "$@" .html`

#END Makefile
