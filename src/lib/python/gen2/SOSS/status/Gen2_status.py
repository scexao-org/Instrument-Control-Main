#
# Gen2_status -- Retrieve status from Gen2
#
# Eric Jeschke (eric@naoj.org)  last edit: 2006.06.01
#
#
import sys

import remoteObjects as ro

import common
import Convert


class g2StatusObj(common.baseStatusObj):
    """ Implements a Python dictionary interface to the Gen2 status system.

    This kind of object does not cache results, and ALWAYS makes a new
    remoteObjects call.

    Example usage:
    ...
    import SOSS.status as st
    ...
    status = st.g2StatusObj('status')

    print status['TSCS.AZ']
    """
    
    def __init__(self, svcname='status', host=None,
                 suppress_fetch_errors=False,
                 suppress_conversion_errors=False):

        super(g2StatusObj, self).__init__()

        self.svcname = svcname

        # holds all kinds of data about SOSS status aliases 
        self.info = Convert.statusInfo()

        if host:
            ro.init([host])
        else:
            ro.init()

        self.reset()


    def get_statusInfo(self):
        return self.info
        

    def reset(self, svcname=None):

        if not svcname:
            svcname = self.svcname
            
        self.statusObj = ro.remoteObjectProxy(svcname)


    def get_statusValue(self, aliasname, allow_fail=True):

        try:
            val = self.statusObj.fetchOne(aliasname)

        except ro.remoteObjectError, e:
            if allow_fail:
                val = common.STATERROR
            else:
                raise common.statusError(str(e))

        valDict = { aliasname: val }
        if common.ro_long_fix:
            valDict = common.ro_unsanitize(valDict)
        
        return valDict[aliasname]


    def get_statusValuesList(self, aliasnames):

        statusDict = {}.fromkeys(aliasnames, common.STATERROR)
        
        try:
            valDict = self.statusObj.fetch(statusDict)

        except ro.remoteObjectError, e:
            raise common.statusError(str(e))

        if common.ro_long_fix:
            valDict = common.ro_unsanitize(valDict)

        res = []
        for alias in aliasnames:
            res.append(valDict[alias])
        
        return res

        
    def get_statusValuesDict(self, resDict):

        statusDict = {}.fromkeys(resDict.keys(), common.STATERROR)
        
        try:
            valDict = self.statusObj.fetch(statusDict)

        except ro.remoteObjectError, e:
            raise common.statusError(str(e))

        if common.ro_long_fix:
            valDict = common.ro_unsanitize(valDict)

        resDict.update(valDict)
        
        return resDict

        
    def set_statusValuesDict(self, statusDict):

        if common.ro_long_fix:
            valDict = common.ro_sanitize(statusDict)
        else:
            valDict = statusDict

        try:
            self.statusObj.store(valDict)

        except ro.remoteObjectError, e:
            raise common.statusError(str(e))

        
    def set_statusValue(self, alias, val):
        
        self.set_statusValuesDict({ alias: val })


    #########################################################
    # For compatability with Gen2
    #########################################################
    #
    def fetch(self, statusDict, allow_fail=True):
        # TEMP: ignore allow_fail
        return self.get_statusValuesDict(statusDict)
        
    def fetchList(self, aliasnames, allow_fail=True):
        # TEMP: ignore allow_fail
        return self.get_statusValuesList(aliasnames)
        
    def store(self, statusDict):
        return self.set_statusValuesDict(statusDict)

    def fetchOne(self, alias, allow_fail=True):
        return self.get_statusValue(alias, allow_fail=allow_fail)
        
    def storeOne(self, alias, val):
        return self.set_statusValueDict({ alias: val })
        
        
#END
