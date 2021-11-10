#
# Makefile for python/tools directory
#
# Bruce Bon     2008-07-11
#
# Almost empty now, but should be expanded to include other .py files
#

TESTABLE_PYTHON_FILES =  

NONTESTABLE_PYTHON_FILES =  SOSS_db.py dbtool.py

TEST_PY_FILES := $(TESTABLE_PYTHON_FILES:%.py=test_%.py)

ALL_PYTHON_FILES := $(TESTABLE_PYTHON_FILES) $(TEST_PY_FILES) \
		    $(NONTESTABLE_PYTHON_FILES)

PYDOC_FILES := $(ALL_PYTHON_FILES:%.py=%.html)

default: Makefile $(ALL_PYTHON_FILES)

all: default doc

doc: $(PYDOC_FILES)

clean: Makefile
	rm -f *.pyc $(PYDOC_FILES)

cleanall: Makefile clean cleandoc
	rm -f *.log

cleandoc: Makefile
	rm -f $(PYDOC_FILES)


# test:  testunit
# testall: test

# testunit: default
#       PYTHONPATH=./:.. \
#	   ../test_all.py $(TEST_PY_FILES)

update:
	@echo updating ./
	svn up

$(PYDOC_FILES): %.html : %.py
	PYTHONPATH=../.. \
	   pydoc.py -w `basename "$@" .html`

#END
