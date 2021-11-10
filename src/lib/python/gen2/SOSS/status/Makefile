#
# Makefile for SOSS status module
# eric@naoj.org
#
# Bruce Bon     2007-06-01
#
RPC_X_FILES = OSSC_ScreenGet.x TCSS.x TCSL.x TCSV.x

RPC_GEN_FILES := $(RPC_X_FILES:%.x=%constants.py) \
		 $(RPC_X_FILES:%.x=%packer.py) \
		 $(RPC_X_FILES:%.x=%types.py) \
		 parsetab.py
#RPC_GEN_FILES = OSSC_ScreenGetconstants.py OSSC_ScreenGetpacker.py 
#                   OSSC_ScreenGettypes.py

DEF_FILES = StatusAlias.def StatusTSCV.def

TESTABLE_PYTHON_FILES =  SOSS_status.py

NONTESTABLE_PYTHON_FILES = $(RPC_GEN_FILES) screenPrint.py parsetab.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

COVERAGEREPORT = coverage.txt
ANNOTATED_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=cover_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
						$(NONTESTABLE_PYTHON_FILES)

DOC_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES)

PYDOC_FILES := $(DOC_PYTHON_FILES:%.py=%.html)

#PYTHON_INC=/usr/include/python2.5
PYTHON_INC=/usr/include/python2.6

.PHONY: default all clean test doc

default: $(RPC_GEN_FILES) $(DEF_FILES)

all: doc default

doc: $(RPC_GEN_FILES) $(PYDOC_FILES)

$(RPC_GEN_FILES):      ../../rpcgen.py $(RPC_X_FILES)
	@for file in $(RPC_X_FILES) ; do \
	    ../../rpcgen.py $$file ; \
	done

StatusAlias.def: StatusAlias.pro
	-/bin/rm StatusAlias.def
	./pro2def.py --in=StatusAlias.pro --out=StatusAlias.def

StatusTSCV.def: 
	-/bin/rm StatusTSCV.def
	./pro2def.py --tscv --out=StatusTSCV.def

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

	@for f in $(TESTABLE_PYTHON_FILES); do \
	  echo Annotating $$f; \
	  ../../coverage.py -a $$f; \
	done

	../../coverage.py -r $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) > $(COVERAGEREPORT)
	cat $(COVERAGEREPORT)

RUBBISH = $(RPC_GEN_FILES) $(DEF_FILES) *.pyc *.pyo *~ *.BAK \
	parser.out parsetab.py

clean:
	-rm -f $(RUBBISH) $(PYDOC_FILES) $(RPC_GEN_FILES)
	-rm -f $(ANNOTATED_PY_FILES) .coverage $(COVERAGEREPORT)

# Added a PYTHONPATH so the rpc gen files will build html properly - yuck
$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=../../ pydoc.py -w `basename "$@" .html`

#END Makefile
