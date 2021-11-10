#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Aug  5 15:27:32 HST 2008
#]
#
"""

This module provides a process object abstraction for simplifying Unix
process management in Python programs.

The interface provides the following functions, variables and exceptions:

myproc.
  status() -- 
  wait() --
  reason() --
  signal(signum) --
  kill() --
  output() --
  stdin -- open file object for WRITING to the subprocess' stdin,
           unless one was passed in, in which case this is null
  stdout -- open file object for READING from the subprocess' stdout,
           unless one was passed in, in which case this is null
  stderr -- open file object for READING from the subprocess' stderr,
           unless one was passed in, in which case this is null

"""

import os, sys, time

try:
    MAXFD = os.sysconf('SC_OPEN_MAX')
except (AttributeError, ValueError):
    MAXFD = 256

default_shell = '/bin/sh'


class myprocError(Exception):
    """Class for raising exceptions in myproc module.
    """
    pass


# Convenience function for having the child process try to run a command.
#
def exec_cmd(cmd, env=None, addenv=False, close_fds=False):
    """
    Exec a command.  This will transform the current process into a new
    one.  The call does not return unless the exec fails.  Usually raises
    an OSError if the call to exec fails.
    
    Parameters:
      cmd: may be a string or a list.  If a string, it is a command string
      that will be invoked via the user's SHELL.  If a list, it is a list
      of command and arguments.

      env: the environment as a mapping (e.g. a dict).  If None, the
      current environment is ihherited.

      addenv: if True, then the variables in env will AUGMENT the current
      environment, and not replace it.
      
      close_fds: if True, then all open file descriptors except stdin,
      stdout and stderr are closed immediately before the exec.
    """

    # If cmd is a list, then that's the list for execv, otherwise
    # user probably wants a shell to run the command
    if isinstance(cmd, basestring):
        shell = os.environ['SHELL']
        if not shell:
            shell = default_shell

        cmd = [shell, '-c', cmd]

    # Close all open file descriptors to avoid resource leaks
    if close_fds:
        for i in range(3, MAXFD):
            try:
                os.close(i)
            except OSError:
                pass

    if not env:
        newenv = os.environ

    elif addenv:
        # User wants variables passed to augment the current environment.
        newenv = {}
        newenv.update(os.environ)
        #newenv.update(env)
        # env values may not be strings!
        for (key, val) in env.items():
            newenv[key] = str(val)

    else:
        newenv = {}
        # env values may not be strings!
        for (key, val) in env.items():
            newenv[key] = str(val)

    prog = cmd[0]
    #prog = cmd.pop(0)
    
    return os.execve(prog, cmd, newenv)


def write_pidfile(filepath, pid):
    try:
        pid_f = open(filepath, 'w')
        pid_f.write("%d\n" % pid)
        pid_f.close()

    except IOError, e:
        raise myprocError("Failed to open/write pid file: %s" % str(filepath))


def read_pidfile(filepath):
    try:
        pid_f = open(filepath, 'r')
        pid = int(pid_f.read().strip())
        pid_f.close()

        return pid

    except IOError, e:
        raise myprocError("Failed to open/read pid file: %s" % str(filepath))


def testloop():
    import time
    while True:
        print "Yessir!"
        time.sleep(1.0)
        
        
class myproc(object):

    # myproc constructor.
    #
    def __init__(self, fn, args=[], kwdargs={},
                 stdin=None, stdout=None, stderr=None,
                 env=None, addenv=False, close_fds=False,
                 detach=False, doublefork=False,
                 usepg=False, pidfile=None):

        self.dead = True
        self.detach = detach
        self.exitcode = 0
        self.pid = 0
        self.stat = 'never-started'
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.usepg = usepg
        # Amount to sleep by increments
        self.sleep_incr = 0.1

        mypid = os.getpid()
        exitcode = 0
        try:
            # Create pipes as necessary for communication
            if detach or doublefork:
                rdfd, wdfd = os.pipe()
            if not stdin:
                rinfd, winfd = os.pipe()
            if not stdout:
                routfd, woutfd = os.pipe()
            if not stderr:
                rerrfd, werrfd = os.pipe()

            # Fork a process and grab the pid.
            pid = os.fork()
            if pid == 0:
                # CHILD

                # Do extra work if child wants to be started as a daemon.
                if detach:
                    os.close(rdfd)
                    # Decouple from parent environment.
                    os.chdir("/") 
                    # ?????
                    #os.umask(0) 
                    os.setsid() 

                if detach or doublefork:
                    # Do second fork.
                    try: 
                        pid = os.fork() 
                        if pid > 0:
                            # FIRST CHILD (SECOND PARENT)
                            try: 
                                # Write pid of *our* child to *our* parent, who will
                                # read it and put it in the myproc object.
                                tmp_f = os.fdopen(wdfd, 'w')
                                tmp_f.write("%d\n" % pid)
                                tmp_f.close()

                                # reap possible dead child
                                childpid, exitcode = os.waitpid(pid, os.WNOHANG)

                            except Exception, e:
                                sys.stderr.write ("(%d) first child error: %s\n" % \
                                                  (os.getpid(), str(e)))
                                sys.stderr.write ("(%d) first child exit.\n" % \
                                                  (os.getpid()))
                                sys.exit(exitcode) # Exit second parent.

                    except OSError, e: 
                        sys.stderr.write ("(%d) fork #2 failed: (%d) %s\n" % \
                                          (os.getpid(), e.errno, e.strerror))
                        try:
                            tmp_f = os.fdopen(wdfd, 'w')
                            tmp_f.write("%d\n" % os.getpid())
                            tmp_f.close()
                        finally:
                            sys.exit(1)

                    except Exception, e: 
                        sys.stderr.write ("(%d) fork #2 failed: %s\n" % \
                                          (os.getpid(), str(e)))
                        try:
                            tmp_f = os.fdopen(wdfd, 'w')
                            tmp_f.write("%d\n" % os.getpid())
                            tmp_f.close()
                        finally:
                            sys.exit(1)

                #<== Success: (child)

                # CHILD (cont)--now either first or second child
                if doublefork or usepg:
                    # Reset our process group, so that child processes
                    # are grouped with us and can be killed together.
                    os.setpgid(0, os.getpid())

                if detach or doublefork:
                    # Parent was the one that needed this fd, so close it
                    os.close(wdfd)

                # Redirections, if desired.
                # If we were not handed a descriptor for stdin then duplicate
                # the pipe end for stdin onto our stdin.
                if not stdin:
                    os.dup2(rinfd, sys.stdin.fileno())
                    os.close(winfd)
                else:
                    # If stdin is a string then treat it as a file to open
                    # for stdin, otherwise we assume it is an already open
                    # file object
                    if type(stdin) == str:
                        stdin = open(stdin, 'r')
                    if stdin.fileno() != sys.stdin.fileno():
                        os.dup2(stdin.fileno(), sys.stdin.fileno())

                # ditto, stdout
                if not stdout:
                    os.dup2(woutfd, sys.stdout.fileno())
                    os.close(routfd)
                else:
                    if type(stdout) == str:
                        stdout_name = stdout
                        stdout = open(stdout, 'a')
                        # If user specified same name for stderr, then share
                        # the fd
                        if stdout_name == stderr:
                            stderr = stdout
                    if stdout.fileno() != sys.stdout.fileno():
                        os.dup2(stdout.fileno(), sys.stdout.fileno())

                # ditto, stderr
                if not stderr:
                    os.dup2(werrfd, sys.stderr.fileno())
                    os.close(rerrfd)
                else:
                    if type(stderr) == str:
                        stderr = open(stderr, 'a')
                    if stderr.fileno() != sys.stderr.fileno():
                        os.dup2(stderr.fileno(), sys.stderr.fileno())

                # Close all open file descriptors to avoid resource leaks
                if close_fds:
                    for i in range(3, MAXFD):
                        try:
                            os.close(i)
                        except OSError:
                            pass

                # If we were created with a callable, then call it
                if callable(fn):
                    if addenv and (env != None):
                        # augment the current environment.
                        os.environ.update(env)

                    # Ideally, this calls its own sys.exit and never returns
                    fn(*args, **kwdargs)

                else:
                    # otherwise assume it is a command to invoke
                    try:
                        exec_cmd(fn, env=env, addenv=addenv,
                                 close_fds=close_fds)
                        
                    except OSError, e: 
                        exitcode = e.errno
                        sys.stderr.write("Failed to exec '%s'\n" % str(fn))

            elif pid > 0:
                # PARENT
                if detach or doublefork:
                    # Read pid of our child's child, because it was double-forked
                    # as a daemon.
                    os.close(wdfd)
                    tmp_f = os.fdopen(rdfd, 'r')
                    self.pid = int(tmp_f.read().strip())
                    tmp_f.close()

                    # Wait for our child, which should have exited right after
                    # writing IT'S child's pid, otherwise we get a zombie...
                    childpid, self.exitcode = os.waitpid(pid, 0)
                    self.dead = True
                    self.stat = 'detached'
                else:
                    self.pid = pid
                    self.dead = False

                if pidfile != None:
                    write_pidfile(pidfile, self.pid)

                # Map pipe descriptors to Python file objects
                if not stdin:
                    self.stdin = os.fdopen(winfd, 'w')
                    os.close(rinfd)

                if not stdout:
                    self.stdout = os.fdopen(routfd, 'r')
                    os.close(woutfd)

                if not stderr:
                    self.stderr = os.fdopen(rerrfd, 'r', 0)
                    os.close(werrfd)

                # Find out what happed to child.
                self.__update_status()

            else:
                # fork() failed.  Record the error return code.
                self.exitcode = pid

        finally:
            # If we spawned any new processes, kill them here.
            if os.getpid() != mypid:
                sys.exit(exitcode)
            else:
                # TODO: reap processes?
                pass
            

    #end __init__()


    # Our printed representation is the output of the process.
    def __str__(self):
        return self.output()

    
    # Query and return the status of our process.
    # Return values: exited, exited-with-signal, stopped, running
    #
    def status(self, waitflag=None):

        self.__update_status(waitflag)
        
        return self.stat


    def wait(self, timeout=None):
        """Wait for completion of child process and return its status.
        """

        if timeout == None:
            self.__update_status(waitflag=1)
            return self.stat

        end_time = time.time() + timeout
        self.__update_status()
        while (self.stat == 'running') and (time.time() < end_time):
            # Sleep for a bit
            time.sleep(self.sleep_incr)
            
            self.__update_status()
            
        return self.stat


    def waitpg(self, timeout=None):
        """Wait for completion of process group and return its status.
        """

        if timeout == None:
            # Wait for main process
            status = self.wait(timeout=None)

            # <-- PG leader no longer running.  Now checking status
            # of child processes
            status = 'running'
            while (status == 'running'):
                # Sleep for a bit
                time.sleep(self.sleep_incr)
            
                status = self.statuspg()

            return status
            
        else:
            end_time = time.time() + timeout

            # Check status of pg leader
            status = self.wait(timeout=timeout)

            # If PG leader still running by end of wait period
            # report it
            if (time.time() > end_time) and (status == 'running'):
                return status

            # <-- PG leader no longer running.  Now checking status
            # of child processes
            status = 'running'
            while (status == 'running') and (time.time() < end_time):
                # Sleep for a bit
                time.sleep(self.sleep_incr)
            
                status = self.statuspg()
            
            return status


    def getpid(self):
        """Return the PID associated with this process.
        """
        return self.pid


    def getexitcode(self):
        """Get the exit code of the process.
        """
        self.__update_status()
        if self.stat.startswith('exited'):
            return self.exitcode

        raise myprocError("Process has not yet exited!")


    def reason(self):
        """Return the reason that the process changed status.  Return value
        must be interpreted relative to the status:
        never-started: error code
        running: None
        exited: exit code of the process via exit()
        exited-with-signal: signal that caused the process to die
        stopped: signal that caused the process to stop
        """
    
        self.__update_status()

        if self.stat == 'running':
            return None

        if self.stat == 'exited':
            return os.WEXITSTATUS(self.exitcode)

        if self.stat == 'exited-with-signal':
            return os.WTERMSIG(self.exitcode)

        if self.stat == 'stopped':
            return os.WSTOPSIG(self.exitcode)

        # Must have never started.
        return self.exitcode


    def signal(self, signum):
        """Send the process a signal.  _signum_ indicates the signal as
        defined in the Python 'signal' module.
        """

        self.__update_status()
        
        if self.dead:
            raise myprocError('process has already exited')

        try:
            os.kill(self.pid, signum)

            self.__update_status()

        except OSError, e:
            raise myprocError(str(e))
        

    def signalpg(self, signum):
        """Send the process group a signal.  _signum_ indicates the signal as
        defined in the Python 'signal' module.
        """

        self.__update_status()
        
##         if self.dead:
##             raise myprocError('process has already exited')

        try:
            os.killpg(self.pid, signum)

            self.__update_status()

        except OSError, e:
            raise myprocError(str(e))
        

    def kill(self):
        """Terminate the subprocess with prejudice.
        """

        self.signal(signum=9)
            
        # This will reap the process.
        self.status(waitflag=1)
            

    def killpg(self):
        """Terminate the process group with prejudice.
        """

        self.signalpg(signum=9)
        
        # This will reap the process.
        self.status(waitflag=1)


    # Get the output of the process.  This is only practical for moderate
    # levels of output.
    #
    def output(self):
        self.__update_status()
        
        if self.stdout:
            return self.stdout.read()
        
        else:
            raise myprocError("process object was passed an explicit stdout")
            

    # Get the stderr of the process.  This is only practical for moderate
    # levels of output.
    #
    def error(self):
        self.__update_status()
        
        if self.stderr:
            return self.stderr.read()
        
        else:
            raise myprocError("process object was passed an explicit stderr")
            

    # Query and update the internal status of our process.
    #
    def __update_status(self, waitflag=None):
        if self.dead:
            return

        if waitflag:
            waitarg = 0
        else:
            waitarg = os.WNOHANG

        # This will raise an OSError if there is a bad pid given.
        try:
            pid, status = os.waitpid(self.pid, waitarg)

        except OSError, e:
            self.dead = True
            self.exitcode = 0
            self.stat = 'exited-unknown'
            return

        if pid == self.pid:

            if os.WIFEXITED(status):
                self.dead = True
                self.exitcode = status
                self.stat = 'exited'
                return

            if os.WIFSIGNALED(status):
                self.dead = True
                self.exitcode = status
                self.stat = 'exited-with-signal'
                return

            if os.WIFSTOPPED(status):
                self.exitcode = status
                self.stat = 'stopped'
                return

        # By process of elimination, assume we are still running.
        self.stat = 'running'


    def statuspg(self):
        """Get the status of a process group.  If *all* processes have
        terminated then return 'exited', else return 'running'.
        """
        
        # This will reap dead children, if using a process group
        try:
            pid = -1
            while (pid != 0):
                # This will raise an OSError if there is a bad pid given.
                pid, status = os.waitpid(-self.pid, os.WNOHANG)
                #if pid != 0:
                #    print "REAPED pid=%d status=%d" % (pid, status)
                    

            return 'running'
        
        except OSError, e:
            errmsg = "[Errno 10] No child processes"
            if errmsg == str(e):
                #print "NO CHILDREN"
                return 'exited'
            raise e


#END myproc

class getproc(object):

    # Get information about a process.
    # TODO: this should eventually harvest information from the /proc
    # filesystem, and find out a lot more detailed status, which can be
    # queried.
    #
    def __update_status(self):

        p = myproc('ps -p ' + str(self.pid) + ' -o pid=')
        output = p.output()
        s = p.status()        # Force reap
        if output:
            self.dead = False
            self.stat = 'running'
            return

        # By process of elimination, assume we are exited.
        self.dead = True
        self.stat = 'exited'
        return

       
    # getproc constructor.
    #
    def __init__(self, pid=os.getpid(), pidfile=None):

        if pidfile != None:
            self.pid = read_pidfile(pidfile)
        else:
            self.pid = pid
        self.dead = True
        self.exitcode = 0
        self.stat = 'unknown'

        self.__update_status()
        

    # Query and return the status of our process.
    # Return values: exited, running
    #
    def status(self):

        self.__update_status()
        
        return self.stat


    # Send the process a signal.
    #
    def signal(self, signum):

        self.__update_status()
        
        if self.dead:
            raise myprocError('process does not exist')

        os.kill(self.pid, signum)

        self.__update_status()
        

    # Send the process group a signal.
    #
    def signalpg(self, signum):

        self.__update_status()
        
        if self.dead:
            raise myprocError('process does not exist')

        os.killpg(self.pid, signum)

        self.__update_status()
        

    # Terminate the process.
    #
    def kill(self):

        self.signal(signum=9)


    # Terminate the process group.
    #
    def killpg(self):

        self.signalpg(signum=9)



#END myproc

