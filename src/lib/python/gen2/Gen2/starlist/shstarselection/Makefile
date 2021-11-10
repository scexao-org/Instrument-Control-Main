#
#	Makefile : makefile for SUBARU
#	2005.03.23
#

#                                 target: Program/Library
PROGRAM	= QDASvgwShStarSelection
SRCS	= QDASvgwShStarSelection.c QDASvgwShStarSelectionReadCfg.c \
 QDASvgwShCalcPreference.c QDASvgwShStarSelectionTool.c

OPTION = -g 

all : $(PROGRAM) $(LIBRARY)

        CPPFLAGS	= -I.
        CFLAGS	= $(CPPFLAGS) $(OPTION)

        OBJS	= $(SRCS:.c=.o)

        LOPT	= -lm 

        MKDEP	= makedepend
        CP	= cp
        RM	= rm -f


#                            make library
$(PROGRAM) : $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LOPT)

#                            make library
$(LIBRARY) : $(OBJS)
	$(AR) -ruv $@ $(OBJS)

.c.o :
	$(CC) $(CFLAGS) -c $*.c

clean :
	$(RM) $(PROGRAM) $(LIBRARY) $(SRCS:.c=.o) Makefile.bak



