import sys
from webapp.helper import log
from webapp.helper import inspectDict

def cache(payAttentionTo = None, ignore = None):
    def _cache(func):
        def wrapper_do_function(*args, **kwargs):
            try:
                parent = args[0]
            except:
                raise
            assert isinstance(parent, Hashable), 'Only Hashable datatypes are possible'
            kwargsToCheck = [l for l in list(func.__code__.co_varnames) if l != 'self']
            interestingKwargs = {}
            if type(kwargsToCheck) != type(None):
                interestingKwargs = {kwarg: kwargs[kwarg] if kwarg in kwargs else None for kwarg in kwargsToCheck}
            else:
                interestingKwargs = kwargs
            parDict = inspectDict(parent)
            localAttribute = 'attr-loc-'
            if payAttentionTo != None:
                for attr in list(payAttentionTo):
                    interestingKwargs['{}{}'.format(localAttribute, attr)] = '{}'.format(parDict[attr] if attr in parDict else 'None')
            ignored = list(ignore) if type(ignore) != type(None) else []
            globalAttribute = 'attr-glo-'
            if parent.alwaysCheck != None:
                for attr in [att for att in list(parent.alwaysCheck) if att not in ignored]:
                    if attr not in interestingKwargs and '{}{}'.format(localAttribute, attr) not in interestingKwargs:
                        interestingKwargs['{}{}'.format(globalAttribute,attr)] = '{}'.format(parDict[attr] if attr in parDict else 'None')
            hashable = '{}__{}'.format(func.__name__, '__'.join(['{}_{}'.format(k, interestingKwargs[k]) for k in interestingKwargs]))
            already, ret = parent.isHashedAlready(hashable)
            if already:
                return ret
            result = func(*args, **kwargs)
            parent.insertNewResult(hashable, result)
            return result
        return wrapper_do_function
    return _cache


class Hashable:
    internalStore={}
    storageSize = 1000
    verbose = False
    alwaysCheck = None
    
    def __init__(self, storageSizeInMB = 1000, verbose = True, alwaysCheck = None):
        self.storageSize = storageSizeInMB
        self.verbose = verbose
        self.alwaysCheck = alwaysCheck
    
    def isHashedAlready(self, hashable):
        exists = hashable in self.internalStore
        if self.verbose and exists:
            log('Reuse result from earlier with')
            log('\t{}'.format(hashable))
        return exists, self.internalStore[hashable] if exists else None
    
    def insertNewResult(self, hashable, result):
        size = sys.getsizeof(self.internalStore)
        for key in self.internalStore:
            size += sys.getsizeof(self.internalStore[key])
        if self.verbose:
            log('Current size of internal storage:\t{} Bytes'.format(size))
        if size / 1024 / 1024 >= self.storageSize:
            if self.verbose:
                log('Deleting internalStore due to overrunning storage')
            keys = list(self.internalStore.keys())
            for key in keys:
                del self.internalStore[key]
        self.internalStore[hashable] = result
