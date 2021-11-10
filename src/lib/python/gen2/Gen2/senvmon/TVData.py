#!/usr/bin/env python
#
# TVData
# Time-Value data storage
# This class stores time-value pairs & can provide
# min & max values used to scale the display in a time-value data view
#
# I use ListMixin to duck type a list clone that is implemented with
# 2 lists, but it changes input and output data so it
# takes {tuples containing time-value pairs} & returns a list of tuples.
#
# fixme: The list must remain sorted by time, but this is never asserted.
# It's fine if you just append data in order, stamped with a sane clock.

from __future__ import division

import ListMixin
import time
from bisect import bisect, bisect_left
from RuntimeDecisionEngine import *


class TVData(ListMixin.ListMixin):
    ''' Time-Value data store, use List interface to store sorted time-value tuples. '''
    def __init__(self, L=[]):
        self.T = map(lambda TV:TV[0], L)
        self.V = map(lambda TV:TV[1], L)

    def _constructor(self, iterable):
        return TVData(iterable)

    def __len__(self):
        return len(self.T)

    def _get_element(self, i):
        assert 0 <= i < len(self)
        return (self.T[i], self.V[i])

    def _set_element(self, i, x):
        assert 0 <= i < len(self)
        self.T[i] = x[0]
        self.V[i] = x[1]

    def _resize_region(self, start, end, new_size):
        assert 0 <= start <= len(self)
        assert 0 <= end   <= len(self)
        assert start <= end
        self.T[start:end] = [None] * new_size
        self.V[start:end] = [None] * new_size

    # This method will cull old data
    # It only really culls when the data is well beyond the threshold, so that
    # it rearranges the storage infrequently
    def cullDataOlderThan(self, maxSeconds):
        now = time.time()
        oldDate = now - (maxSeconds * 1.5)
        try:
            oldestData = self.T[0]
        except IndexError:
            # ok, no time value data yet
            return
        if oldestData < oldDate:
            cullDate = now - maxSeconds
            i = bisect_left(self.T, cullDate)
            del self[:i]


    def minMaxForTimeRange(self, startTime, endTime):
        ''' unoptimized scan for min & max values within timerange '''
        i, j = self.indiceesForTimeRange(startTime, endTime)

        minval = maxval = None
        try:
            for n in xrange(i,j):
                value = self.V[n]
                if value == None:
                    continue
                if (minval == None or value < minval):
                    minval = value
                if (maxval == None or value > maxval):
                    maxval = value
            return (minval, maxval)
        except Exception, e:
            print "minMaxForTimeRange raised: ", e
            pass
        return (None, None)

    def indexForTime(self, time):
        return bisect(self.T, time)

    def leftIndexForTime(self, time):
        return bisect_left(self.T, time)

    def indiceesForTimeRange(self, startTime, endTime):
        i = self.leftIndexForTime(startTime)
        j = self.indexForTime(endTime)
        #print "indiceesForTimeRange returning %s:%s" % (str(i), str(j))
        return (i, j)

    def tvDataForTimeRange(self, startTime, endTime):
        i, j = self.indiceesForTimeRange(startTime, endTime)
        # return a generator rather than a new sublist
        #return self[i,j]
        for n in xrange(i,j):
            yield self[n]

    def tvDataForIndicees(self, i, j):
        for n in xrange(i,j):
            yield self[n]

        
    
class MinMaxBucket(object):
    ''' A lightweight data structure for cacheing the minmax 
        values of a time-value datastore. '''
    # I don't intend that these objects have any behaviour, they are 
    # directly manipulated by the keeper of the cache

    # slots breaks pickle, flush cache before pickling
    __slots__ = ('minval', 'maxval', 'index1', 'containsNone')
    
    # SIZE is the default number of elements to be cached in a bucket, 
    # buckets must always be contiguous in a cache level
    SIZE = 32
    def __init__(self, minval=None, maxval=None, index1=0, containsNone=False):
        self.minval = minval
        self.maxval = maxval
        self.index1 = index1
        self.containsNone = containsNone
        
    def __str__(self):
        return "Minmax:(%s,%s)  index:(%s)  containsNone:%s" % \
               (self.minval,self.maxval, self.index1, self.containsNone)

    def minMax(self):
        return (self.minval, self.maxval)

    def minMaxNone(self):
        return (self.minval, self.maxval, self.containsNone)

class BucketIndexComparator(object):
    ''' instances can be compared against MinMaxBucket starting indexes.
        Used to do a binary search of the cache lists '''
    def __init__(self, val):
        self._value = val
    def __cmp__(self, other):
        if isinstance(other, MinMaxBucket):
            return cmp(self._value, other.index1)
        else:
            return cmp(self._value, other)
    def __str__(self):
        return "<%s>: %s" % (self.__class__.__name__, self._value)

class BucketEndComparator(object):
    ''' instances can be compared against MinMaxBucket starting indexes.
        When compared to a cachelevel's cache list via bisect_left,
        will provide the index of the bucket to contain this comparator's value
        Used to do a binary search of the cache lists '''
    def __init__(self, val, bucketSize):
        # my index value for comparison against a MinMaxBucket starting index
        self._value = val
        self._bucketSize = bucketSize
    def __cmp__(self, other):
        if isinstance(other, MinMaxBucket):
            return cmp(self._value - (self._value % self._bucketSize), other.index1)
        else:
            return cmp(self._value, other)
    def __str__(self):
        return "<%s>: %s" % (self.__class__.__name__, self._value)
    
class CTVData(TVData, Decider):
    ''' Cached Time-Value data store, use List interface to store sorted time-value tuples. '''
    # This subclass builds a tree of minMax values to provide a cached minMax answer,
    # obviating a full list scan for a common query (minMaxForTimeRange)
    # The cache is built on demand, and is built as a list of lists of buckets that partition
    # the dataStore's indexes into a regular static tree, keeping minMax ranges for everything
    # under every level of the tree.  To answer the minMaxForTimeRange query, we get as much
    # of the answer as high in the cache as we can, then accumulate a list with the ultimate answer
    # by walking lower levels of the cache.  Each cache walk involves a binary search to find the
    # cache indicees, followed by a short cache walk.  The lookup is intended to be as fast as possible
    # and it enables me to auto-range my data for any time interval.  I also use it heavily to reduce
    # a large data set when I zoom out.  When I have many data points per pixel, I look for cache-aligned
    # values to give a precise answer in a cache friendly, inexpensive way.
    # Fixme: why accumulate minMax list rather than immediately reduce result?
    #
    # I slept through Knuth a long time ago but intuition suggests that:
    #    The cost of rendering the raw data increases linearly with the number of points in the view
    #       and the number of points in the view increases exponentially with the time scale: Order n squared
    #    The cost of calculating minMaxForTimeRange() from the raw data is O(n squared) WRT time scale
    # Once the cache is built,
    #    Cost of calculating minMaxForTimeRange() for graph scaling and point plotting is O(n log n) WRT time scale
    #    Cost of rendering minMaxRegionsforTimeRange() increases linearly with graph area, so it's constant for
    #        a fixed graph size.
    # So rendering from the cache becomes a big win on a large data set, but the cache lookup has to be fast because
    # it will get hit hard.
    #
    # I can't escape the notion that a good lisp hack could rewrite the cache as a one-line lambda, but this
    # is left as an exercise for the reader.
    
    def __init__(self, L=[]):
        TVData.__init__(self)
        # the cache is a list of lists of MinMaxBuckets
        self.flushCache()
        # cache buckets must be aligned, but alignment will move with data deletion
        # not using this for now since I flush the cache on deletion
        #self._cacheAlignmentOffset = 0
        self._bucketCapacity = MinMaxBucket.SIZE

    def flushCache(self):
        ''' recreates the cache as empty list '''
        self.cache = []

    def _resize_region(self, start, end, new_size):
        TVData._resize_region(self, start, end, new_size)
        # This is suboptimal, but rather tricky to solve, so I punt
        if ((end - start) > new_size) or ((len(self.cache)>0) and end < (self.cache[0][-1].index1 + self._bucketCapacity)):
            # deleted data (or inserted data prior to last cached value); 
            # could 'just' eliminate the related cache buckets and reindex
            # all the cache buckets, but I'll just flush the whole cache
            #print "Flushing TVData cache! start:%d end:%d newSize:%d" % (start, end, new_size)
            self.flushCache()
            # if deletion only happens at the beginning of data & insertion
            # only at the end (and I didn't flush the cache), I would do this:
            # if (start == 0):
            #     self._cacheAlignmentOffset -= ((end-start) - new_size)

    def minMaxFromMinMaxList(self, mmList):
        ''' returns minMax from a list of minMax pairs '''
        # doesn't have any instance variables, but maybe instance method will work better for cython
        minval = maxval = None
        for small, big in mmList:
            if ((minval == None or small < minval) and (small != None)):
                minval = small
            if ((maxval == None or big > maxval) and (big != None)):
                maxval = big
        return (minval, maxval)
    
    def minMaxNoneFromMinMaxNoneList(self, mmnList):
        ''' returns (min,max,containsNone) from a list of minMaxNone triplets '''
        # doesn't use any instance variables, but maybe instance method will work better for cython
        minval = maxval = None
        containsNone = False

        for small, big, thisOneHasNone in mmnList:
            # Note that the thisOneHasNone flag is authoritative, and that small or 
            # big of None is a soft error condition, indicating null range failures, 
            # not that the set contains None (though the whole range might be all None's(?) yuck)
            # fixme: so there's an improbable problem here, but a worse problem if null ranges
            # propegate up the cache as a range with a None value; I hate to do more exceptional 
            # type comparisons though, so punt for now
            if thisOneHasNone==True:
                containsNone = True
            if ((minval == None or small < minval) and (small != None)):
                minval = small
            if ((maxval == None or big > maxval) and (big != None)):
                maxval = big
        return (minval, maxval, containsNone)
    
    def _minMaxNoneForIndicees(self, i, j):
        ''' uncached scan for min, max, and None values within indicees '''
        minval = maxval = None
        containsNone = False
        try:
            for n in xrange(i,j):
                value = self.V[n]
                if value == None:
                    containsNone = True
                    continue
                if (value < minval or minval == None):
                    minval = value
                if (value > maxval or maxval == None):
                    maxval = value
            return (minval, maxval, containsNone)
        except Exception, e:
            print "minMaxNoneForIndicees raised: ", e
            pass
        return (None, None, False)

    def _minMaxForIndicees(self, i, j):
        ''' uncached scan for min & max values within indicees '''
        #minval, maxval, containsNone = self._minMaxNoneForIndicees(i, j)
        #return (minval, maxval)
        return self._minMaxNoneForIndicees(i, j)[:2]

    def _minMaxNoneIndiceesAtLevel(self, i, j, cacheLevel):
        ''' Returns (min,max,containsNone,start,stop) using data from a single cache level. 
            Start & stop are the bounding indicees for the data provided by this cache level. 
            CacheLevel is -1 for uncached data, and this private method does not build cache '''

        #if self.decide("debug", "cache", Decider.SUSPECT):
        #    print "ENTER _minMaxNoneIndicees:%d %d AtLevel:%d" % (i,j, cacheLevel)

        if cacheLevel == -1:
            minval, maxval, containsNone = self._minMaxNoneForIndicees(i, j)
            #if self.decide("debug", "cache", Decider.SUSPECT):
            #    print "minMaxNoneIndicees:%d %d AtLevel:%d returns %s %s" % (i,j, cacheLevel, minval, maxval)
            return (minval, maxval, containsNone, i, j)

        buckets = self.cache[cacheLevel]
        # start will be the index of the first bucket at or after i
        start = bisect_left(buckets, BucketIndexComparator(i))
        if (start >= len(buckets)) or buckets[start].index1 >= j:
            return (None, None, False, i, i)
        bucketSize = self._bucketCapacity ** (cacheLevel+1)
        # end will be the index of the bucket to contain j
        end = bisect_left(buckets, BucketEndComparator(j, bucketSize))
        if (end <= start):
            return (None, None, False, i, i)

        minval, maxval, containsNone = \
              self.minMaxNoneFromMinMaxNoneList((buckets[ndx].minMaxNone() for ndx in xrange(start,end)))
        
        endIndex = buckets[start].index1 + ((end-start)*bucketSize)

        #if self.decide("debug", "cache", Decider.SUSPECT):
        #    print "minMaxNoneIndicees:%d %d AtLevel:%d returns %s %s" % (i,j, cacheLevel, minval, maxval)
        #    print "    search up for %d-%d %d-%d" % (i, buckets[start].index1, endIndex, j)

        assert endIndex <= j
        return (minval, maxval, containsNone, buckets[start].index1, endIndex)

    
    def _cachedMinMaxNoneAtLevel(self, i, j, cacheLevel):
        ''' returns minMaxNone list for data with indicees using data from a single cache level '''
        ''' cacheLevel is -1 for uncached data, and this private method does not build cache '''
        #minval, maxval, containsNone, startIndex, stopIndex = self._minMaxNoneIndiceesAtLevel(i, j, cacheLevel)
        #return (minval, maxval, containsNone)
        return self._minMaxNoneIndiceesAtLevel(i, j, cacheLevel)[:3]
    
    def _buildCache(self, i, j):
        ''' build the cache for indexes i to j, starting with small buckets, to as big as necessary '''
        cacheLevel = 0
        bucketSize = self._bucketCapacity
        createdNewBuckets = False
        
        while True:
            iRoundup = i + bucketSize - 1
            iBucketStart = iRoundup - (iRoundup % bucketSize)
            jBucketEnd = (j - (j % bucketSize))

            if bucketSize > (jBucketEnd - iBucketStart):
                break
            
            # there must be >= 1 bucket at this cache level
            
            # ensure we have a list of buckets at this cache level
            if len(self.cache) == cacheLevel:
                # add a list to the cache stack for buckets at this level
                self.cache.append([])
            # buckets is the list of MinMaxBuckets at the current cacheLevel
            buckets = self.cache[cacheLevel]

            # if there are no cache buckets or the first cache bucket precedes the
            # start index by a bucketsize or more...
            if (len(buckets) == 0) or (buckets[0].index1 >= i + bucketSize):
                # we must create some new buckets and insert them at the head of this cacheLevel
                newBuckets = []
                if len(buckets) == 0:
                    startIndex = iBucketStart
                    endIndex = jBucketEnd
                else:
                    firstCachedIndex = buckets[0].index1
                    newBucketCount = (firstCachedIndex - i) // bucketSize
                    startIndex = firstCachedIndex - (newBucketCount * bucketSize)
                    endIndex = firstCachedIndex
                    '''
                    if (cacheLevel > 0):
                        print "--==-> 1stCachedInd:%d i:%d bucketSize:%d" % (firstCachedIndex, i, bucketSize)
                        print "       startIndex:%d  endIndex:%d" % (startIndex, endIndex)
                    '''

                # Now build the cache buckets from the data one level higher
                for bucketIndex in xrange(startIndex, endIndex, bucketSize):
                    minval, maxval, containsNone = self._cachedMinMaxNoneAtLevel(bucketIndex, \
                                                        bucketIndex + bucketSize, cacheLevel-1)
                    '''
                    if (cacheLevel > 0):
                        print " o0o0o creating bucket, level:%d index:%d minmax:(%s,%s)" % \
                              (cacheLevel, bucketIndex, str(minval), str(maxval))
                    '''
                    newBuckets.append(MinMaxBucket(minval, maxval, bucketIndex, containsNone))
                # insert the new cache entries at the beginning of the cache
                buckets[0:0] = newBuckets
                createdNewBuckets = True

            lastCachedIndex = buckets[-1].index1 + bucketSize
            if (lastCachedIndex <= j - bucketSize):
                #print "================================"
                #print "lastCachedIndex:%d j:%d bucketsize:%d cacheLev:%d" % (lastCachedIndex, j, bucketSize, cacheLevel)
                
                # we must create some new buckets and insert them at the tail of this cacheLevel
                # build the cache buckets from the data one level higher
                #for bucketIndex in xrange(lastCachedIndex, j, bucketSize):
                bucketIndex = lastCachedIndex
                while (bucketIndex+bucketSize) <= j:
                    #in xrange(lastCachedIndex, j, bucketSize):
                    #print "XXXXX creating bucket at %s" % bucketIndex
                    minval, maxval, containsNone = self._cachedMinMaxNoneAtLevel(bucketIndex, \
                                                        bucketIndex + bucketSize, cacheLevel-1)
                    buckets.append(MinMaxBucket(minval, maxval, bucketIndex, containsNone))
                    bucketIndex += bucketSize
                createdNewBuckets = True
                
            # break if I don't create any buckets at this level
            # because I won't create any more at higher cache levels
            if not createdNewBuckets:
                break
                
            cacheLevel += 1
            bucketSize *= self._bucketCapacity

    def _rawCacheLookup(self, i, j):
        ''' returns (minval, maxval, containsNone) from the cache for the data from index i to j
        This method doesn't build the cache, caller ensured cache was sufficient (_buildCache) before calling _rawCacheLookup
        '''
        minMaxNoneList = []
        cacheLevel = len(self.cache)-1
        while True:
            minval, maxval, containsNone, index1, index2 = \
                  self._minMaxNoneIndiceesAtLevel(i,j,cacheLevel)
            # if no results from this cache level, repeat the query at lower cache level
            if (i == index1 == index2) and cacheLevel >= 0:
                cacheLevel -= 1
                continue
            minMaxNoneList.append((minval, maxval, containsNone))
            break

        # lowIndex1 = i
        lowIndex2 = index1
        highIndex1 = index2
        # highIndex2 = j
        #if self.decide("debug", "cache", Decider.SUSPECT):
        #    print "    lowInd2:<<%d>> hiInd1:%d" % (lowIndex2, highIndex1)

                
        # This lowside/high side walk can only work after a successful
        # lookup higher in the cache
        lowTreeDone = (lowIndex2 == i)
        highTreeDone = (highIndex1 == j)
        while cacheLevel >= 0:
            if lowTreeDone and highTreeDone:
                break
            
            cacheLevel -= 1
            
            #if self.decide("debug", "cache", Decider.SUSPECT):
            #    print "  cache lookups level:%d i:%d lowInd2:{{%d}} hiInd1:%d j:%d" \
            #          % (cacheLevel, i, lowIndex2, highIndex1, j)
                
            if not lowTreeDone:
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    working low tree"
                minval, maxval, containsNone, lowIndex2, dummy = \
                   self._minMaxNoneIndiceesAtLevel(i,lowIndex2,cacheLevel)
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    after low tree, lowIndex2=%d" % (lowIndex2)

                minMaxNoneList.append((minval, maxval, containsNone))
                lowTreeDone = (lowIndex2 == i)

            if not highTreeDone:
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    working high tree"
                minval, maxval, containsNone, dummy, highIndex1 = \
                   self._minMaxNoneIndiceesAtLevel(highIndex1,j,cacheLevel)

                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    after high tree, highIndex1=%d" % (highIndex1)

                minMaxNoneList.append((minval, maxval, containsNone))
                highTreeDone = (highIndex1 == j)

        return self.minMaxNoneFromMinMaxNoneList(minMaxNoneList)


    def _rawCacheBoundaryLookup(self, i, j, coolTime):
        ''' returns (minval, maxval, containsNone, highIndex) from the cache for the data from index i to j
        Ceases looking when the high index has sufficiently advanced, allowing this algorithm to not deeply descend into the cache
        This method doesn't build the cache, caller ensured cache was sufficient (_buildCache) before calling _rawCacheLookup
        '''
        # Fixme: I think the minMaxNoneList is a clever waste; it only exists to be reduced, why not
        # accumulate & reduce it on the fly?
        minMaxNoneList = []
        cacheLevel = len(self.cache)-1
        while True:
            minval, maxval, containsNone, index1, index2 = \
                  self._minMaxNoneIndiceesAtLevel(i,j,cacheLevel)
            # if no results from this cache level, repeat the query at lower cache level
            if (i == index1 == index2) and cacheLevel >= 0:
                cacheLevel -= 1
                continue
            minMaxNoneList.append((minval, maxval, containsNone))
            break

        # lowIndex1 = i
        lowIndex2 = index1
        highIndex1 = index2
        # highIndex2 = j
        #if self.decide("debug", "cache", Decider.SUSPECT):
        #    print "    lowInd2:<<%d>> hiInd1:%d" % (lowIndex2, highIndex1)

                
        # This lowside/high side walk can only work after a successful
        # lookup higher in the cache
        lowTreeDone = (lowIndex2 == i)
        highTreeDone = (highIndex1 == j) or (self.T[highIndex1] >= coolTime)
        while cacheLevel >= 0:
            if lowTreeDone and highTreeDone:
                break
            
            cacheLevel -= 1
            
            #if self.decide("debug", "cache", Decider.SUSPECT):
            #    print "  cache lookups level:%d i:%d lowInd2:{{%d}} hiInd1:%d j:%d" \
            #          % (cacheLevel, i, lowIndex2, highIndex1, j)
                
            if not lowTreeDone:
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    working low tree"
                minval, maxval, containsNone, lowIndex2, dummy = \
                   self._minMaxNoneIndiceesAtLevel(i,lowIndex2,cacheLevel)
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    after low tree, lowIndex2=%d" % (lowIndex2)

                minMaxNoneList.append((minval, maxval, containsNone))
                lowTreeDone = (lowIndex2 == i)

            if not highTreeDone:
                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    working high tree"
                minval, maxval, containsNone, dummy, highIndex1 = \
                   self._minMaxNoneIndiceesAtLevel(highIndex1,j,cacheLevel)

                #if self.decide("debug", "cache", Decider.SUSPECT):
                #    print "    after high tree, highIndex1=%d" % (highIndex1)

                minMaxNoneList.append((minval, maxval, containsNone))
                highTreeDone = (highIndex1 == j) or (self.T[highIndex1] >= coolTime)

        return list(self.minMaxNoneFromMinMaxNoneList(minMaxNoneList)) + [highIndex1]



    def cachedMinMaxNone(self, i, j):
        ''' builds as much of the bucket cache as necessary and returns (minval, maxval, containsNone) '''
        self._buildCache(i,j)
        return self._rawCacheLookup(i,j)
    
    def cachedMinMax(self, i, j):
        ''' builds as much of the bucket cache as necessary and returns (minval, maxval) '''
        minval, maxval, containsNone = self.cachedMinMaxNone(i, j)
        return (minval, maxval)


    def minMaxForTimeRange(self, startTime, endTime):
        i, j = self.indiceesForTimeRange(startTime, endTime)
        return self.cachedMinMax(i,j)


    def minMaxRegionsForTimeRange(self, startTime, endTime, width, maxInterval):
        # I assume suitable cache was already built by scaling query prior to this invocation
        timeInterval = endTime - startTime
        #widthPerTime = width / timeInterval
        timePerPixel = timeInterval / width
        i, j = self.indiceesForTimeRange(startTime, endTime)
        timeCursor = startTime
        while i < j:
            n = self.indexForTime(timeCursor + maxInterval)
            coolTime = timeCursor + timePerPixel
            if n == i:
                n += 1
            minval, maxval, containsNone, highIndex = self._rawCacheBoundaryLookup(i, n, coolTime)
            if highIndex < j:
                lastTime = self.T[highIndex]
            else:
                lastTime = endTime

            #print "minMaxRegionsForTimeRange yeilding: (%s %s %d %d)" % (str(minval), str(maxval), timeCursor, lastTime)
            yield (minval, maxval, containsNone, timeCursor, lastTime)

            i = highIndex
            timeCursor = lastTime

        

        
        
        
        
        
        
        

    