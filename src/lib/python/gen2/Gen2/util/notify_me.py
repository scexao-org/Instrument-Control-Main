#!/usr/bin/env python

import os
import sys
import time
import datetime

import ssdlog

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

def __mailing_you(sub, sndr, rcpt, msg, logger=None):

    mail = MIMEText('%s' %msg)  
    mail['Subject'] = sub
    mail['From'] = sndr
    mail['To'] = rcpt

    s = smtplib.SMTP('mail.subaru.nao.ac.jp')
    if logger:
        logger.debug('sending email...')
    try:
        s.sendmail(sndr, [rcpt], mail.as_string())
        s.quit()
    except Exception as e:
        if logger:
            logger.error('error: sending a mail. %s' %(e))


def notify_snmp(msg, logger=None):
    ''' mailing snmp trap '''

    now=datetime.datetime.now()

    subject='Summit UPS  %s' %(now.strftime('%Y-%m-%d %H:%M:%S'))
    sender='tinagaki@naoj.org'
    recipient='ocs@naoj.org'
 
    __mailing_you(sub=subject, sndr=sender, rcpt=recipient, msg=msg, logger=logger)
  

def notify_me(sub, sndr, rcpt, msg, logger=None):
    ''' general usage of mailing '''

    __mailing_you(sub, sndr, rcpt, msg, logger=logger)

def main(options,args):
 
    logname = 'email'
    logger = ssdlog.make_logger(logname, options)

    subject='TEST'
    sender='tinagaki@naoj.org'
    recipient='ocs@naoj.org'

    today=datetime.datetime.today()
    msg='%s\nmailing to you...' %today.strftime("%Y-%m-%d %H:%M:%S")

    notify_me(sub=subject, sndr=sender, rcpt=recipient,  msg=msg, logger=logger)
    notify_snmp(msg, logger)

if __name__ == "__main__":

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")

    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    #if len(args) > 0:
    #    optprs.error("incorrect number of arguments")
       
    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

