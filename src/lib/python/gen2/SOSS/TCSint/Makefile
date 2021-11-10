#
# Makefile for SOSS Instrument Interface module
#[ Eric Jeschke (eric@naoj.org) --
#]
#
# Bruce Bon     2007-06-01
#
RPCINT  = TowardTSCpacker.py TowardTSCtypes.py TowardTSCconstants.py

.PHONY: default all clean test doc

default: all

all: $(RPCINT) 


$(RPCINT):      ../../rpcgen.py TowardTSC.x
	../../rpcgen.py TowardTSC.x
	@echo "Nothing to do!"

RUBBISH = *.pyc *.pyo *~ 

clean:
	-rm -f $(RUBBISH)

#END Makefile
