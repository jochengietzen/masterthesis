import numpy as np
import pandas as pd
import math
import inspect as ins
import os


def envCheck(env, alternative = None):
    return os.environ[env] if env in os.environ else alternative

def envValueCheck(env, value):
    return envCheck(env) == value

def log(*args):
    import sys
    print(*args, file=sys.stdout)

def valueOrAlternative(kwargs, key, alternative=None):
    return kwargs[key] if key in kwargs else alternative

def keyValuesFilter(dic, keys):
    return {key: dic[key] for key in keys if key in list(dic.keys())}


def consecutiveDiff(x, checkNum = None, extended = True):
    tmp = np.array([0] + list(np.where(np.ediff1d(((x == checkNum) if checkNum != None else x).astype(int)) != 0)[0] + 1) + [len(x)])
    tmp = zip(tmp, tmp[1:])
    if extended:
        tmp = [((t[0], t[1]), (x[t[0]], t[1] - t[0])) for t in tmp]
    return tmp


def adjusted_window(i, maxval, max_timeshift):
    negWin = math.floor(max_timeshift/2)
    posWin = math.ceil(max_timeshift/2)
    lower = max(0, i - negWin)
    upper = min(maxval, i + posWin)
    adjust = (max_timeshift - (upper-lower))
    if adjust > 0 and lower > 0:
        lower = max(0, lower - adjust)
    elif adjust > 0 and upper < maxval:
        upper = min(maxval, upper + adjust)
    return (lower, upper)

def slide_time_series(toslide, column_id, column_sort, rolling_direction = 1, max_timeshift = None, column_kind=None):
    ids = toslide[column_id].unique()
    srld = []
    for idd in ids:
        subtoslide = toslide[toslide[column_id] == idd].copy()
        subtoslide.sort_values(by=column_sort, inplace=True)
        subtoslide.reset_index(drop=True, inplace=True)
        #subslid = pd.DataFrame({col: [] for col in subtoslide.columns.to_list()})
        max_timeshift = max_timeshift if max_timeshift != None else subtoslide.shape[0]
        #windowborders = [(i, min(i+max_timeshift, subtoslide.shape[0])) for i in range(subtoslide.shape[0])]
        windowborders = [adjusted_window(i, maxval=subtoslide.shape[0], max_timeshift=max_timeshift) for i in range(subtoslide.shape[0])] 
        if rolling_direction < 0:
            windowborders = [(i, max(i-max_timeshift, 0)) for i in range(subtoslide.shape[0], 0, -1)]
        ssrld = []
        for tIndex, (b0, b1) in enumerate(windowborders):
            subsubslid = subtoslide.iloc[b0:b1, [i for i, col in enumerate(subtoslide.columns.to_list()) if col != column_id]]
            subsubslid[column_id] = subtoslide.loc[tIndex, column_sort]
            ssrld.append(subsubslid)
        subslid = pd.concat(ssrld)
        if column_kind != None and column_kind != column_id:
            subslid[column_kind] = idd
        elif len(ids) > 1:
            column_kind = 'newID'
            subslid['newID'] = idd
        subslid = subslid.reindex(columns=[column_id, column_sort] + [col for col in subslid.columns.to_list() if col not in [column_id, column_sort]])
        subslid.reset_index(drop = True, inplace=True)
        srld.append(subslid)
    subslid = pd.concat(srld)
    return subslid

def specificKwargs(kwargs, specifics): 
    return {key: kwargs[key] if key in kwargs else specifics[key] for key in specifics.keys() if key in kwargs or type(specifics[key]) != type(None)}

def alternativeMap(arr, mapping, alternative):
    return np.array([alternative if elem not in mapping else mapping[elem] for elem in arr])


def inspect(Class):
    """
    Function to inspect classes. Gives you all attributes of given class
    """
    return [att[0] for att in ins.getmembers(Class, lambda a: not(ins.isroutine(a))) if not(att[0].startswith('__') and att[0].endswith('__'))]

def inspectTuple(Class):
    """
    Function to inspect classes. Gives you all attributes and their values of given class
    """
    return [att for att in ins.getmembers(Class, lambda a: not(ins.isroutine(a))) if not(att[0].startswith('__') and att[0].endswith('__'))]

def inspectDict(Class):
    """
    Function to inspect classes. Gives you all attributes and their values of given class as dictionary
    """
    return {att[0]: att[1] for att in inspectTuple(Class)}
    
def castlist(elem):
    """
    Casts any object into list, without making a list into ndlist
    """
    if type(elem) == str:
        return [elem]
    if type(elem) == type(None):
        return []
    if type(elem) == list:
        return elem
    return list(elem)