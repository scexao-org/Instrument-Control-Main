__version__ = "$Revision:$"
# $Source:$
# $Author:$
import Util
import datetime, calendar
import logging
logger = logging.getLogger('TCSInterface.Packet')

TZ_UTC   = Util.FixedOffset(0, "UTC")
TZ_LOCAL = Util.LocalTimezone()

def TCSTimeStringToDatetime(timestr):
    '''TCS time string is in the form of yyyyMMddhhmmddsss. The value
    is in UTC time zone.
    This function will convert the string to a crresponding datetime object. 
    '''
    year   = int(timestr[0:4])
    month  = int(timestr[4:6])
    day    = int(timestr[6:8])
    hour   = int(timestr[8:10])
    min    = int(timestr[10:12])
    sec    = int(timestr[12:14])
    musec  = int(timestr[14:15]) * 100000
    dt = datetime.datetime(year = year, 
                           month = month, 
                           day = day, 
                           hour = hour,
                           minute = min, 
                           second = sec,
                           microsecond = musec, 
                           tzinfo = TZ_UTC)
    return dt

def datetimeToTCSTimeString(dateTime):
    '''
    converts a datetime object (internal representaion of the time)
    to the TCS time string fromat.
    @param dateTime the datetime object to convert to the TCS time string.
    '''
    dateTime = dateTime.astimezone(TZ_UTC)
    _date = dateTime.date()
    _time = dateTime.time()
    return '%4.4d%2.2d%2.2d%2.2d%2.2d%2.2d%1.1d'%(_date.year,
                                                  _date.month,
                                                  _date.day,
                                                  _time.hour,
                                                  _time.minute,
                                                  _time.second,
                                                  int(_time.microsecond / 100000.0))
    
def calculateProjectedCompletionDatetime(timeStr, currentTime):
    '''
    @param timeStr     6 bytes string of hhmmss format that represents the 
                       projected completion time
    @param currentTime datetime object that represent the time the packet is 
                       sent.  The completion time is calculated relative to 
                       this datetime.
    @throws ValueError if the timeString is not of proper format.
    '''
    h = int(timeStr[:2])
    m = int(timeStr[2:4])
    s = int(timeStr[4:6])
    compTime = currentTime.replace(hour = h, 
                                   minute = m,
                                   second = s,
                                   microsecond = 0)
    # The time string does not have date field. In case the completion time
    # is across the date boundary, 24 hours must be added to the time.
    if currentTime > compTime:
        compTime = compTime + datetime.timedelta(days=1)
    return compTime
        
class PacketParser:
    def __init__(self):
        self.payloadParsers = {}
 
    def setHeaderParser(self, headerParser):
        self.headerParser = headerParser

    def addPayloadParser(self, payloadParser, callBack = None):
        self.payloadParsers[(payloadParser.packetType,
                             payloadParser.messageType)] = (payloadParser, callBack)

    def parse(self, packetString):
        headerString = packetString[:self.headerParser.headerLength]
        payloadString = packetString[self.headerParser.headerLength:]
        header  = self.headerParser.parse(headerString)
        (payloadParser, callBack) = self.payloadParsers[(header.getPacketType(),
                                                         header.getMessageType())]

        payload = payloadParser.parse(payloadString, header)
        if callBack:
            try:
                callBack(header, payload)
            except TypeError, e:
                logger.error("call back function failed. %s"%(str(e)))
                raise
        logger.debug('the PacketParser object parsed the packet header =%s : payload=%s'%(header.format(),
                                                                                          payload.format()))
        return header, payload

class TSCHeader:
    def __init__(self,
                 messageType=None,
                 sender=None,
                 receiver=None,
                 pid=None,
                 timeSent=None,
                 lenPayload = 0):
        self.messageType = messageType
        self.sender = sender
        self.receiver = receiver
        self.pid = pid
        self.timeSent = timeSent
        self.lenPayload = lenPayload

    def format(self):
        return "%2.2s%4.4s%4.4s%04.4d%15.15s%4.4d"%(self.messageType,
                                                    self.receiver + '%' * (4 - len(self.receiver)),
                                                    self.sender   + '%' * (4 - len(self.sender)),
                                                    self.pid,
                                                    datetimeToTCSTimeString(self.timeSent),
                                                    self.lenPayload)

    def getMessageType(self):
        return self.messageType

    def getPacketType(self):
        return None

class TSCHeaderParser:
    headerLength = 33
    def parse(self, str):
        header = TSCHeader()
        header.messageType = str[0:2]
        header.receiver    = str[2:6].strip('%')
        header.sender      = str[6:10].strip('%')
        if str[10:14].strip('%') == '':
            header.pid = 0
        else:
            header.pid = int(str[10:14].strip('%'))
        header.timeSent    = TCSTimeStringToDatetime(str[14:29])
        header.lenPayload  = int(str[29:33])
        return header

class CommandRequestPayload:
    def __init__(self, seqNum=None, commandId=None, commandParam=None):
        self.seqNum = seqNum
        self.commandId = commandId
        self.commandParam = commandParam

    def format(self):
        return "%6.6X%6.6s%s"%(self.seqNum, self.commandId, self.commandParam)

class TSCPayloadParser:
    packetType = None
    def __init__(self):
        pass

class CommandRequestPayloadParser(TSCPayloadParser):
    messageType = "CD"
    
    def parse(self, str, header):
        payload              = CommandRequestPayload()
        payload.seqNum       = int(str[0:6], 16)
        payload.commandId    = str[6:12]
        payload.commandParam = str[12:]
        return payload

class CommandAckPayload:
    def __init__(self,
                 seqNum                  = None,
                 commandId               = None,
                 receiptNum              = None,
                 projectedCompletionTime = None):
        '''
         @param seqNum                  integer value for the command sequence number
         @param commandId               string for the command id (e.g. 1A9001)
         @param receiptNum              integer value for the command recipt number.
         @param projectedCompletionTime datetime object of projected completion time 
        '''
        self.seqNum = seqNum
        self.commandId = commandId
        self.receiptNum = receiptNum
        self.projectedCompletionTime = projectedCompletionTime

    def format(self):
        # This probably is not correct. But as long as we use
        # FAI simulator, this kludge is needed.
        if self.projectedCompletionTime is None:
            hour = 'NN'
            min = 'NN'
            sec = 'NN'
        else:
            hour ='%2.2d' % self.projectedCompletionTime.time().hour
            min = '%2.2d' % self.projectedCompletionTime.time().minute
            sec = '%2.2d' % self.projectedCompletionTime.time().second
        return "%6.6X%6.6s%6.6X%2.2s%2.2s%2.2s%2.2s"%(self.seqNum,
                                            self.commandId,
                                            self.receiptNum,
                                            'OK',
                                            hour,
                                            min,
                                            sec
                                            )

class CommandNackPayload:
    def __init__(self,
                 seqNum=None,
                 commandId=None,
                 errorCode = None):
        '''
         @param seqNum    integer value for the command sequence number
         @param commandId string for the command id (e.g. 1A9001)
         @param errorCode integer value cause of the failure (see telescope documentation).
        '''
        self.seqNum = seqNum
        self.commandId = commandId
        self.errorCode = errorCode

    def format(self):
        return "%6.6X%6.6s%6.6s%2.2s%6.6s"%(self.seqNum,
                                            self.commandId,
                                            'NNNNNN',
                                            'NG',
                                            self.errorCode)

class CommandAckPayloadParser(TSCPayloadParser):
    messageType = "CA"
    def parse(self, str, header):
        if str[18:20] == "OK":
            payload = CommandAckPayload()

            try:
                payload.receiptNum = int(str[12:18], 16)
            except ValueError, e:
                # Dunno why but the simulator sometimes returns ------ for the receipt number 
                logger.warn('Received wrong numerical string for receipt number: %s'%str[12:18])
                payload.receiptNum = 0
                
            try:
                payload.projectedCompletionTime = \
                    calculateProjectedCompletionDatetime(str[20:26], header.timeSent)
            except ValueError, e:
                # ValueError means the projected completion time has
                # wrong numerical string format
                logger.warn('Received wrong numerical string for projected completion time: %s'%str[20:26])
                payload.projectedCompletionTime = None

        elif str[18:20] == "NG":
            payload = CommandNackPayload()
            payload.errorCode = str[20:26]

        payload.seqNum     = int(str[0:6], 16)
        payload.commandId  = str[6:12]

        return payload

class CommandCompletionPayloadParser(TSCPayloadParser):
    messageType = "CE"
    
    def parse(self, str, header):
        payload = CommandCompletionPayload()
        payload.seqNum     = int(str[0:6], 16)
        payload.commandId  = str[6:12]
        payload.receiptNum = int(str[12:18], 16)
        payload.resultCode = str[18:28].strip('%')
        payload.resultInfo = str[28:]
        
        return payload
    

class CommandCompletionPayload:
    def __init__(self,
                 seqNum=None,
                 commandId=None,
                 receiptNum=None,
                 resultCode = None,
                 resultInfo = None):
        '''
         @param seqNum     integer value for the command sequence number
         @param commandId  string for the command id (e.g. 1A9001)
         @param receiptNum integer value for the command recipt number.
         @param resultCode string value indicates the result of the 
                command(see telescope documentation).
         @param resultInfo binary buffer (string) of the 
                status on TSC(see telescope documentation).
        '''
        self.seqNum = seqNum
        self.commandId = commandId
        self.receiptNum = receiptNum
        self.resultCode = resultCode
        self.resultInfo = resultInfo

    def format(self):
        return ("%6.6X%6.6s%6.6X%10.10s"%(self.seqNum,
                                          self.commandId,
                                          self.receiptNum,
                                          (self.resultCode + '%%%%%%%%%%')[:10]) 
               + self.resultInfo)
    

class AsyncMessagePayload:
    def __init__(self,
                 msgType=0,
                 msgCode=0,
                 hasText=True,
                 msgText = None):
        self.msgType = msgType
        self.msgCode = msgCode
        self.hasText = hasText
        self.msgText = msgText 

    def format(self):
        '''
        Contrary to what the telescope documentation says, the asynchronous message
        packet is left justified with '%' padded, not white space padded. 
        '''
        if self.hasText:
            numHasText = 1
        else:
            numHasText = 0
        return "%1.1d%06.6d%1.1d%100.100s"%(
            self.msgType,
            self.msgCode,
            numHasText,
            self.msgText + (100 - len(self.msgText)) * '%')
    
class AsyncMessagePayloadParser(TSCPayloadParser):
    messageType = "CM"
    
    def parse(self, str, header):
        payload = AsyncMessagePayload()
        payload.msgType    = int(str[0:1])
        if str[1:7].strip('%') == '':
            payload.msgCode = 0
        else:
            payload.msgCode = int(str[1:7].strip('%'))
        payload.hasText = (str[7:8] == '1')
        payload.msgText = str[8:]
        return payload
