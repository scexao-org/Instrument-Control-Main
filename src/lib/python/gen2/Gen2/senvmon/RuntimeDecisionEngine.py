#!/usr/bin/env python
'''
Runtime Decision Engine
I want a way to tune the code execution based on decisions that can be altered at run or debug time.
The decision making process needs to be settable by decision domain, from the instance level all the
way to the global level.  Decisions need to be made fast so they can be embedded deep in expensive loops,
and the criteria and process need to be clear.

Ideally the decision process creates as little garbage as possible and incurs no expensive code.

When a decision is called for, a Decider will look for reasons to commit to action.  Reasons are specific
to a domain, and a reason consists of a key and a mandate.  A mandate is a value greater than zero and <= 99.
A decider has an "environment" of responses which may be keyed to reasons.  If the reason's mandate plus response
are >= 100, then the decider will take action without further reasoning.   Since mandates cannot be > 99, a 
recalcitrant decider cannot be compelled to act; the decider indicates his enthusiasm for an action by his 
response.  If a decider is to act on all reasons, then his default response should be set to 100.  By 
convention, the default reason is "default".  Note however, that a response to the specific "default"
reason is different than the default response, applied to otherwise insufficient reasons.

Reasons are keyed (scenarios or suggestions) for the decider to consider in order to decide to do something.
I suggest the following interpretation of the range of mandates:
99: almost irresistable mandate, I'd force your decision
80: Do it unless strongly compelled to inaction
50: your choice, but I suggest it
20: It's all you, but I'm interested in your action
10: do it if you feel strongly
 1: only those things you always must do
 
 Conversely, I might provide an environmental default response (reaction) in the "log" domain with
 the following range of values and possible interpretations:
 
 1: chatty (I won't take action unless your reason compels my reluctant chattiness) 
         (cost of inaction low, cost of action high
10: info
20: debug
50: warning
70: suspect
80: problem
90: error
100:fail (take action regardless of reasons)(action important)
        (cost of inaction high, cost of action effectively low)

    #
    coordinator.addReason("log", "default", 80)
    self.addReason("log", "debug", 99)

    common case: I will decide to run debug code when global mandate is high or mandate for this specific 
    class of action is mentioned at any level.

    if self.decide("debug", key="cache", keyAction=Decider.SUSPECT, defaultAction=Decider.DEBUG):
    
Documentation note:
Reason lists are only passively maintained; reasons are only expired if & when they are matched to decisions.
So you don't want to abuse the RDE by accumulating reasons that are not likely to matched in a timely manner.
'''

import time

class Reason(object):
    ''' You won't instantiate a Reason; instead tell your Decider to addReason() and he will
    queue a new reason, and evaluate the reason when he has a suitable decide() '''
    # suggested mandates for your reason
    FORCE = 99
    DOIT = 80
    SUGGEST = 50
    COOL = 20
    IFMUST = 10
    MENTION = 1
    
    def __init__(self, key, mandate, count=None, timeout=None):
        self.key = key
        # sanity check: reason must mandate, cannot force
        mandate = min(mandate, 99)
        if mandate <= 0:
            mandate = 1
        self.mandate = mandate
        self.count = count
        self.expiry = None
        if timeout:
            self.expiry = time.time() + timeout
    
class Decider(object):
    ''' Subclasses of Decider can be given domain specific "reasons", which are simply a key and a
    mandate value.  Reasons can persist until you deleteReason() or they
    can expire after a time period or usage count.
    A Decider can decide() based on a tunable response to reasons that are temporary or permanent,
    instance specific or global.
    '''
    # here are some response levels, think of these as "promise to act if x", so for action in "log" domain,
    # 'I'm chatty, so I'll decide to log if me or my mentor has a reason to compel verbosity"
    # At the other end of the response scale, a response of 100 compels action for any mandate on a matching
    # reason, or any reason for a default response.  In the "log" domain, you might promise to ACT because
    # you're committing to log all FAIL failures.  In other words, the response scale is from inaction (0)
    # to action (100), but I have synonym words here implying motivation to act on negative events requiring
    # logging or debugging
    PASS = 0
    CHATTY = 1
    INFO = 10
    DEFAULT = DEBUG = 20
    WARNING = 50
    SUSPECT = 70
    PROBLEM = 80
    ERROR = 90
    ACT = FAIL = 100
    
    
    def addReason(self, domain, key, mandate, count=None, timeout=None):
        if not (0 < mandate <= 99):
            print "addReason: bad mandate"
            return
        if not hasattr(self, "_reasons"):
            self._reasons = {}
        if not domain in self._reasons:
            self._reasons[domain] = []
        self._reasons[domain].append(Reason(key, mandate, count=count,timeout=timeout))
        
    def deleteReason(self, domain, key, deleteAll=False):
        ''' Attempts to delete a matching reason from the receivers list of reasons
            If deleteAll==True this will delete all matching reasons
        '''
        try:
            for reason in reversed(self._reasons[domain]):
                if reason.key == key:
                    self._reasons[domain].remove(reason)
                    if not deleteAll:
                        break
        # fixme: only catch expected exceptions here
        except Exception, e:
            pass
    
    def _expireReason(self, domain, reason):
        ''' possibly removes the reason, returns True to act on the reason, False to not act on expired reason'''
        if reason.expiry and time.time() > reason.expiry:
            #print "removing reason (timeout):%s" % (reason.key)
            #try:
            # this expired reason just got unmandated so it can't fire no more
            reason.mandate = 0
            self._reasons[domain].remove(reason)
            return False
            #except Exception, e:
            #print "Darn, removing reason %s did:" % (reason.key), e
                
        # if a reason has a countdown, see if you expire this reason as it is acted upon
        if reason.count != None:
            reason.count -= 1
            if reason.count <= 0:
                #print "count removing reason:%s" % (reason.key)
                self._reasons[domain].remove(reason)
        return True

    # In my original idea for the decide method, I intended that my responses would be kept
    # in a dict.  But I couldn't make the design case that I would actually promise a complex
    # set of responses; At the decision point, I make a specific, static commitment to respond
    # to a limited range of reasons (just a single defined response and a default)
    def decide(self, domain, key=None, keyAction=0, defaultAction=20):
        ''' Decide to act based on my reasons and on some set of responses '''
        # first allow my mentor to decide, based on his reasons
        if hasattr(self, "_mentor") and self._mentor.decide(domain, key, keyAction, defaultAction):
            return True

        # Mentor didn't have sufficient reason, evaluate my own reasons
        if hasattr(self, "_reasons") and domain in self._reasons:
            # I run through the reasons in reverse because if the reason has timed out, it will be
            # removed & I will keep iterating for a valid reason
            for reason in reversed(self._reasons[domain]):
                # act if I have a strong specific response to this reason
                if reason.key == key and (reason.mandate + keyAction >= 100):
                    if self._expireReason(domain, reason):
                        return True
                # act if I have a sufficient response in this domain to any compelling mandate
                if reason.mandate + defaultAction >= 100:
                    if self._expireReason(domain, reason):
                        return True
        return False
    
    
    
    