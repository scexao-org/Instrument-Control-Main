Instructions for using the Python Subaru SOSS Instrument Interface
------------------------------------------------------------------
Eric Jeschke (eric@naoj.org)  2006.04.19

This document describes the use of the OBSERVATION CONTROL SYSTEM SIDE
(e.g. SOSS, Gen2) of the OCS-instrument interface.  In particular, the
INSint.py interface and the associated GUI tester INSintTester.py.

USAGE
-----
There are two ways to use the interface: using the GUI tester
(INSintTester.py), and as a standalone program with a remote object
interface (INSint.py). 

USING INSintTester.py
---------------------
For instrument interface testing or debugging the interface you can run
the program 'INSintTester.py'.  This brings up a graphical interface in
which you can specify the interface configuration parameters, start and
stop the interface, and view the RPC packet communication logs.

It has a window from which you can send commands to the instrument.  If
a real SOSS status source is available it can supply that as status if
the instrument requests status.  FITS images can be transferred.  There
is nothing else connected to the interface on the OCS side, so it is of
use for interactive testing and debugging purposes only.

Use the --help option to see the possible command-line options:

$ ./INSintTester.py --help
Usage: INSintTester.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  --debug               Enter the pdb debugger on main()
  -d DIR, --fitsdir=DIR
                        Use DIR for storing instrument FITS files
  -m NAME, --monitor=NAME
                        Reflect internal status to monitor service NAME
  --numthreads=NUM      Use NUM threads for each interface
  --obcphost=HOST       Use HOST as the OBCP host
  -n NUM, --obcpnum=NUM
                        Use NUM as the OBCP number
  -P PASSWORD, --password=PASSWORD
                        Use PASSWORD for ftp transfers
  --profile             Run the profiler on main()
  -s FILE, --statusfile=FILE
                        Use FILE for providing SOSS status
  --statushost=HOST     Use HOST for obtaining SOSS status
  --statussvc=SVCNAME   Use SVCNAME for obtaining Gen2 status
  -t TRANSFERMETHOD, --transfermethod=TRANSFERMETHOD
                        Use METHOD (ftp|rpc|ssh) for transferring FITS files
                        (OBCP must support method)
  -u USERNAME, --username=USERNAME
                        Login as USERNAME@obcp for ftp/ssh transfers

Most of the command line options can be set from the GUI, so it is not
necessary to use them.  The description of these options is in the
section of this readme on INSint.py.

Typical use is to start the INSintTester as follows:

$ ./INSintTester &

The program should start off displaying two GUI windows: a window titled
"Commands" and another titled "SOSS/OBCP Interface Tester".  From the
interface tester window, click the "Setup" button to set up the
parameters for communicating to the OBCP.  Then click the "Start" button
to start the interfaces.  You should see logging output in each of the
four panes of the tester window.

To load a device dependent command file, click the "Load Cmds" button in
the Commands window toolbar.  Select a command file in the dialog.  To
send a command to the instrument, select the text of the command with
the mouse and click "Send Line".  You should be able to see RPC
transactions progressing in the interface window.

The "Quit" button in either window will stop the servers and terminate
the application.


USING INSint.py
---------------
For OCS gen2 it is expected that the interface will be brought up as a
single process by the gen2 system invoking the file 'INSint.py' with the
appropriate options.

NOTE:
When running in this mode as a standalone interface, the remoteObject
system needs to be activated prior to use (remoteObjectNameSvc.py and
remoteObjectManagerSvc.py are already running).  It is expected that the
usual case would be for remoteObjectManagerSvc.py to start this program
when an instrument is 'allocated' (restart it if it fails) and shut it
down when the instrument is 'deallocated'.  This is done via a remote
object call to the remoteObjectManagerSvc.  More on the remote object
interface later in this document.

Command line options
--------------------
$ ./INSint.py --help
Usage: INSint.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -C, --clear           Clear the rpc transaction database on startup
  --db=FILE             Use FILE as the rpc transaction database
  --debug               Enter the pdb debugger on main()
  -d DIR, --fitsdir=DIR
                        Use DIR for storing instrument FITS files
  --hostfilter=HOSTS    Specify a list of HOSTS that can request status
  -i INTERFACES, --interfaces=INTERFACES
                        List of interfaces to activate
  --log=FILE            Write logging output to FILE
  --loglevel=LEVEL      Set logging level to LEVEL
  -m NAME, --monitor=NAME
                        Reflect internal status to monitor service NAME
  --numthreads=NUM      Use NUM threads in thread pool
  --obcphost=HOST       Use HOST as the OBCP host
  -n NUM, --obcpnum=NUM
                        Use NUM as the OBCP number
  -P PASSWORD, --password=PASSWORD
                        Use PASSWORD for ftp transfers
  --port=PORT           Register using PORT
  --profile             Run the profiler on main()
  --statushost=HOST     Use HOST for obtaining SOSS status
  --statussvc=SVCNAME   Use SVCNAME for obtaining Gen2 status
  --stderr              Copy logging also to stderr
  -t TRANSFERMETHOD, --transfermethod=TRANSFERMETHOD
                        Use METHOD (ftp|rpc|ssh) for transferring FITS files
                        (OBCP must support method)
  --svcname=NAME        Register using NAME as service name
  -u USERNAME, --username=USERNAME
                        Login as USERNAME@obcp for ftp/ssh transfers

The command line options configure the parameters of the interface as
follows: 

--fitsdir=PATH
  Specifies a directory in which image FITS files transferred from the
  instrument will be stored by the interface.  The default is to store
  them in the current directory.

--interfaces=<interface-list>
  Specify which of the four instrument sub-interfaces should be activated.
  The <interface-list> should be specified as a comma-separated (no
  spaces!) list of any of the following tokens: cmd,sreq,sdst,file .
  These correspond to the sub-interfaces for commands, status requests
  (from instrument for OCS status), status distribution (instrument
  specific status transmitted to OCS) and FITS file image transfer
  command processing.  The default value is 'cmd,sreq,sdst,file' (all
  four sub-interfaces should be activated).

--hostfilter=HOSTS
  By default, INSint will accept a rpc status packet from any host.
  This option can be used to silently limit the hosts that can send
  status to it.

--numthreads=NUM
  A coarse way to specify the amount of concurrency provided to the
  sub-interfaces.  The default value should be sufficient.

--obcphost=HOST
  Specifies the unqualified (short) hostname of the instrument.  It
  needs to be 8 characters or less, due to bad assumptions on the part
  of SOSS architects.  Your name service needs to be able to resolve
  this name to the IP address of the instrument.  This defaults to the
  short version of the canonical hostname of the local host.

--obcpnum=NUM
  Specifies the Subaru-sanctioned enumeration number of this
  instrument.  This defaults to 9, the number of the default simulation
  instrument ("SUKA").

--log=FILE
  Log output of the interfaces to FILE.

--loglevel=INT
  Specify the logging level used for logging.  The number 0 enables the 
  most verbose reporting.

--stderr
  If specified, indicates that logging output should be copied to
  stderr (in addition to anywhere else it is going).

--transfermethod=ftp|ssh|rpc
  Specifies the image file transfer method for this instrument.
  Possible values are one of: ftp, ssh or rpc.  The instrument must be
  configured properly to use this interface.  The default value of 'ssh'
  will work reliably with any instrument that has the ssh package
  installed and configured for remote, passwordless (key-based) logins
  for the given --username.  'ftp' requires that the OBCP be running an
  FTP daemon, and that the 'wget' utility be installed on the same host
  as INSintTester.  The 'rpc' method requires that the instrument is
  using the RPC mechanism of the DAQtk interface.  Currently only one
  instrument uses this method.  Most use FTP.

--username=LOGINID
  Specifies the user login id for FTP or SSH image transfers.  If ssh
  is used (highly recommended) then this login on the instrument should
  be set up to use passwordless secure key login.  The default is to use
  the login id of the user under which the program is executing.

--password=<passwd>
  Provides a way to specify a password for FTP transfers, if the
  instrument is configured with an FTP server for use in image file
  transfers.  Obviously this is very insecure, as the password is
  visible in process listings, and FTP is not a secure protocol anyway.

--statushost=HOST
  Specifies the host used to supply SOSS status for passing on through
  the instrument status request sub-interface.  Only works if you are
  running from a trusted host that has access to the Subaru SOSS or SOSS
  simulator systems in real-time.  The default is no status host, which
  means that status requests will get undefined status values.

--svcname=NAME
  Register a remoteObjects interface using NAME.  Other users of the
  remoteObjects system will be able to then access the instrument
  interface via this name.  The default is to use 'INSint%d' where %d is
  replaced by the instrument number (as specified with --obcpnum).  Use
  of the default name is highly recommended.  When running as a
  standalone interface, the remoteObject system needs to be activated
  prior to use (remoteObjectNameSvc and remoteObjectMonitorSvc are
  already running).  *This option is only needed for Gen2 testing*.

--statussvc=SVCNAME
  Specifies the remote objects service name used for the Gen2 status
  service.    *This option is only needed for Gen2 testing*.

--monitor=SVCNAME
  Specifies the remote objects service name used for reporting to the
  Gen2 monitor service.   *This option is only needed for Gen2 testing*.


Environment variables
---------------------
OSS_SYSTEM
  Required by the status module if fetching status from a real SOSS
  source.  Should be set to the pathname where the SOSS.status module is
  installed or the location of the StatusAlias.def and Table.def files 
  are located.


Example Use
-----------
For testing, the default values will work "out of the box" for testing
on a single host the instrument interface with a simulated instrument:

$ ./INSint.py

If you have access to SOSS status, you may want to supply that option:

$ ./INSint.py --statushost=obs

If you are testing with a real or simulated instrument on another box:

$ ./INSint.py --statushost=obs --obcpnum=7 --obcphost=comics \
--username=comics --transfermethod=ftp --password=youguessedit \
--fitsdir=/data/fits/comics


Remote Object Interface Example
-------------------------------
Assuming that the remote objects system is running on the current system
and the instrument interface has been started:

import remoteObjects as ro
ro.init()
...
inst = ro.remoteObjectProxy('INSint9')
...
inst.send_cmd('EXEC SIMCAM SNAP FRAMENO=SIM90000010 ITIME=10.0'):

<MORE DESCRIPTION OF REMOTE OBJECT INTERFACE TO COME>

