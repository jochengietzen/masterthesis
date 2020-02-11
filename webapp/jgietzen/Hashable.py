import sys
from webapp.helper import log, castlist
from webapp.helper import inspectDict

def cache(payAttentionTo = None, ignore = None):
    '''
    Decorator Function to hash functions of objects of (sub)type Hashable

    Will return the last cached result without executing the function,
    iff it has been calculated with the same kwargs already. 
    Otherwise executes function and saves result in cache.

    Parameters
    ----------
    payAttentionTo : list, optional, default = None 
        A list of strings containing attribute names of the class,
        that need to be watched. E.g. if payAttentionTo = ['bar'] 
        and used in Class Foo, then cache function will check, if 
        foo.bar or one of the kwargs changed.
    
    ignore : list, optional, default = None
        A list of strings containing attribute names of the class,
        that should be ignored for the decorated function. The 
        superclass Hashable allows you to set a always track option 
        of attributes. But if only this decorated function is 
        independent of the always tracked attribute, one can ignore
        it with that option.

    Returns
    -------
    decorator_wrapper : wrapper function
        A decorator wrapper for a function with kwargs.
        

    See Also
    --------
    webapp.jgietzen.Hashable Hashable: Class that defines the cache

   
    Examples
    --------
    >>> Foo(Hashable):
    >>>     def __init__(self):
    >>>         super().__init__()
    >>>         self.bar = 'biz'

    >>>     @cache(payAttentionTo=['bar'])
    >>>     def ret(self):
    >>>         print('run')
    >>>         return self.bar + 'baz'
    
    >>> foo = Foo()
    >>> foo.ret()
    run
    bizbaz
    >>> foo.ret()
    bizbaz
    >>> foo.bar = 'buz'
    >>> foo.ret()
    run
    buzbaz
    '''
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
                for attr in castlist(payAttentionTo):
                    interestingKwargs['{}{}'.format(localAttribute, attr)] = '{}'.format(parDict[attr] if attr in parDict else 'None')
            ignored = list(ignore) if type(ignore) != type(None) else []
            globalAttribute = 'attr-glo-'
            if parent.alwaysCheck != None:
                for attr in [att for att in castlist(parent.alwaysCheck) if att not in ignored]:
                    if attr not in interestingKwargs and '{}{}'.format(localAttribute, attr) not in interestingKwargs:
                        interestingKwargs['{}{}'.format(globalAttribute,attr)] = '{}'.format(parDict[attr] if attr in parDict else 'None')
            hashable = '{}__{}'.format(func.__name__, '__'.join(['{}_{}'.format(k, interestingKwargs[k]) for k in interestingKwargs]))
            if len(args) > 1:
                hashable += '__args__{}'.format('_'.join(str(arg) for arg in args[1:]))
            already, ret = parent.isHashedAlready(hashable)
            if already:
                return ret
            result = func(*args, **kwargs)
            parent.insertNewResult(hashable, result)
            return result
        return wrapper_do_function
    return _cache


class Hashable:
    '''
    Class that implements a hashtable like cache

    Use this class in order to make the decorator function cache 
    available/useable for your class. Don't forget to run 
    super().__init__() in your constructor

    Parameters
    ----------
    storageSizeInMB : int, optional, default = 1000
        Defines the maximum cache space in MB of your Class object
    
    verbose : bool, optional, default = True
        If True, Hashable will produce information output
    
    alwaysCheck : list, optional, default = None
        A list of strings with the attribute names of your class,
        which should be checked for changes everytime a cache 
        decorated function is run.


    See Also
    --------
    webapp.jgietzen.Hashable cache: Decorator function


    ...

    Examples
    --------
    >>> Foo(Hashable):
    >>>     def __init__(self):
    >>>         super().__init__()
    >>>         self.bar = 'biz'

    >>>     @cache(payAttentionTo=['bar'])
    >>>     def ret(self):
    >>>         print('run')
    >>>         return self.bar + 'baz'
    
    >>> foo = Foo()
    >>> foo.ret()
    run
    bizbaz
    >>> foo.ret()
    bizbaz
    >>> foo.bar = 'buz'
    >>> foo.ret()
    run
    buzbaz

    '''
    internalStore={}
    storageSize = 1000
    verbose = False
    alwaysCheck = None
    
    def __init__(self, storageSizeInMB = 1000, verbose = True, alwaysCheck = None):
        self.storageSize = storageSizeInMB
        self.verbose = verbose
        self.alwaysCheck = alwaysCheck
    
    def isHashedAlready(self, hashable):
        '''
        Function that checks if the function was already calculated and
        saved. Returns boolean about the check and the return value of 
        the function, iff exists, otherwise None. 
        '''
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
