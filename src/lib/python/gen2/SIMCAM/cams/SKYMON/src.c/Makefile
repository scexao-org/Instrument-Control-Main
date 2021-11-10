
       PROJHOME = ..
      LOAD_HOME = .

        PROGRAM	= QDASvgwSkyFormatFits
          SRCS	= QDASvgwSkyFormatFits.c 

         OPTION = -g

            CC  =  gcc
            CPP =  gcc
       CPPFLAGS	= -I.
         CFLAGS	= $(CPPFLAGS) $(OPTION)
        LDFLAGS	= -lm
          OBJS	= $(SRCS:.c=.o)
          LIBS	= 

          MKDEP	= makedepend
             CP	= cp
             RM	= rm -f

all : $(PROGRAM)

$(PROGRAM) : $(OBJS) $(LIBS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

.c.o :
	$(CC) $(CFLAGS) -c $*.c

install : $(LOAD_HOME)/$(PROGRAM)

#$(LOAD_HOME)/$(PROGRAM) : $(PROGRAM)
#	$(CP) $(PROGRAM) $(LOAD_HOME)/$(PROGRAM)

clean :
	$(RM) $(PROGRAM) $(SRCS:.c=.o) Makefile.bak

depend : $(SRCS)
	$(MKDEP) $(CPPFLAGS) $(SRCS)

# DO NOT DELETE THIS LINE -- make depend depends on it.

QDASvgwSkyFormatFits.o: /usr/include/stdio.h /usr/include/features.h
QDASvgwSkyFormatFits.o: /usr/include/sys/cdefs.h /usr/include/bits/wordsize.h
QDASvgwSkyFormatFits.o: /usr/include/gnu/stubs.h /usr/include/gnu/stubs-64.h
QDASvgwSkyFormatFits.o: /usr/include/bits/types.h
QDASvgwSkyFormatFits.o: /usr/include/bits/typesizes.h /usr/include/libio.h
QDASvgwSkyFormatFits.o: /usr/include/_G_config.h /usr/include/wchar.h
QDASvgwSkyFormatFits.o: /usr/include/bits/wchar.h /usr/include/gconv.h
QDASvgwSkyFormatFits.o: /usr/include/bits/stdio_lim.h
QDASvgwSkyFormatFits.o: /usr/include/bits/sys_errlist.h /usr/include/stdlib.h
QDASvgwSkyFormatFits.o: /usr/include/sys/types.h /usr/include/time.h
QDASvgwSkyFormatFits.o: /usr/include/endian.h /usr/include/bits/endian.h
QDASvgwSkyFormatFits.o: /usr/include/sys/select.h /usr/include/bits/select.h
QDASvgwSkyFormatFits.o: /usr/include/bits/sigset.h /usr/include/bits/time.h
QDASvgwSkyFormatFits.o: /usr/include/sys/sysmacros.h
QDASvgwSkyFormatFits.o: /usr/include/bits/pthreadtypes.h
QDASvgwSkyFormatFits.o: /usr/include/alloca.h /usr/include/math.h
QDASvgwSkyFormatFits.o: /usr/include/bits/huge_val.h
QDASvgwSkyFormatFits.o: /usr/include/bits/mathdef.h
QDASvgwSkyFormatFits.o: /usr/include/bits/mathcalls.h /usr/include/string.h
QDASvgwSkyFormatFits.o: ./skyfont.h
