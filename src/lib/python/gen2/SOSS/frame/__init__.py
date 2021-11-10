"""SOSS.frame - an interface to the SOSS frame id server.

This module allows you to get FITS frame id's as handed out by the
SOSS frame id service.

Example code to get an A frame for Suprime-Cam:

    import rpc
    import SOSS.frame
    
    try:
        frameSvc = SOSS.frame.rpcFrameObj(frameSvc_host)

    except rpc.PortMapError, e:
        print "Can't connect to portmapper on host (%s)" % frameSvc_host

    ...

    try:
        frameid = frameSvc.get_frame('SPCAM', 'A')

    except SOSS.frame.frameError, e:
    print "Can't pull frame id: %s" % str(e)

"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from SOSS_frame import frameError, rpcFrameObj, OSSS_FRAMEServer


__all__ = ['frameError', 'rpcFrameObj', 'OSSS_FRAMEServer']

