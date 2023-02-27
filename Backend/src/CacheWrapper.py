import random
import sys
from collections import OrderedDict


class CacheWrapper:
    """ The memcache instance, has all functions that will allow the other to manipulate the memcache instance """

    def __init__(self, capacity: int):
        self.memcache = OrderedDict()
        self.capacity = capacity
        self.replace = 'LRU'
        self.accessCount = 0
        self.hit = 0
        self.entryNum = 0
        self.cacheInvalidations = 0

    def get(self, key):
        self.accessCount += 1
        if key not in self.memcache:
            return -1
        else:
            self.hit += 1
            self.memcache.move_to_end(key, last=False)
            return self.memcache[key]

    def put(self, key, value):
        # self.memcache.__setitem__(key, value)
        # self.memcache.update({key, value})

        if self.replace == 'LRU':
            self.LRUReplacement(value)
        else:
            self.RNDReplacement(value)

        self.memcache[key] = value
        self.memcache.move_to_end(key)
        self.entryNum += 1

        # #################
        # for i in  self.memcache:
        #     print(i)
        # #################


    def LRUReplacement(self, value) -> None:
        if len(self.memcache) + 1 > self.capacity:
            self.memcache.popitem(last=False)
            self.entryNum -= 1

    def RNDReplacement(self, value) -> None:
        if len(self.memcache) + 1 > self.capacity:
            replace = random.randint(0, self.capacity)
            index = 0
            keyInd = self.memcache.__iter__()
            while index != replace:
                keyInd = next(keyInd)
                index += 1
            self.memcache.popitem(keyInd)
            self.entryNum -= 1

    def clear(self) -> None:
        self.entryNum = 0
        return self.memcache.clear()

    def invalidate(self, key):
        if key in self.memcache:
            self.memcache.popitem(key)
            self.cacheInvalidations += 1

    def refreshConfigurations(self, capacity: int, replace: str):
        self.capacity = capacity
        self.replace = replace

    def getSize(self):
        # Bytes into database, in case of information loss
        size = 0
        for i in self.memcache:
            size += sys.getsizeof(self.memcache[i])

        return size

    # def displayStats(self):
    #     if(self.accessCount != 0):
    #         return {'capacity': self.capacity,
    #                 'accessCount': self.accessCount,
    #                 'hit': self.hit,
    #                 'entryNum': self.entryNum,
    #                 'hitRatio': self.hit / self.accessCount,
    #                 'cacheInvalidations' : self.cacheInvalidations
    #                 }
    #     else:
    #         return {'capacity': self.capacity,
    #                 'accessCount': self.accessCount,
    #                 'hit': self.hit,
    #                 'entryNum': self.entryNum,
    #                 'cacheInvalidations' : self.cacheInvalidations,
    #                 'replacementPolicy' : self.replace,
    #                 'sizeInMegaByte' : sys.getsizeof(self.memcache)
    #                 }
    #
    #
    #
    # def displayAllKeys(self):
    #     return self.memcache.keys()
