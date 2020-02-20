from webapp.jgietzen.Data import Data
from .applicationProvider import session
from webapp.config import dir_datafiles
from ..helper import log
import os
import re

def getCurrentFile():
    data = Data.load(session.get('file'))
    if type(data) == type(None):
        return None
    return data

def existsData():
    data = getCurrentFile()
    return data != None, data

def existsCurrentFile():
    from os.path import join, exists
    return exists(join(dir_datafiles, session.get('file')))

def saveCurrentFile(df = None, originalfilename = None, column_sort = 'idx', column_id = None, column_outlier = None):
    data = getCurrentFile()
    if type(data) == type(None):
        data = Data(df, column_sort=column_sort, 
            column_id = column_id, column_outlier = column_outlier,
            filename = session.get('file'),
            originalfilename = originalfilename)
        data.save()
    else:
        data.bare_dataframe = df if type(df) != type(None) else data.bare_dataframe
        data.originalfilename = df if type(originalfilename) != type(None) else data.originalfilename
        data.column_id = column_id if column_id != None else data.column_id
        data.column_sort = column_sort if column_sort != None else data.column_sort
        data.column_outlier = column_outlier if column_outlier != None else data.column_outlier
        data.save()

def deleteCurrentFile():
    data = getCurrentFile()
    if type(data) != type(None):
        data.delete()
        session['file'] = None

def getAvailableDataSets():
    return [fil for fil in os.listdir(dir_datafiles) if fil.startswith('datafile_')]

def getAvailableDataSetsAsOptionList():
    return [{'label': re.sub('datafile_', '', fil), 'value': fil} for fil in getAvailableDataSets()]

def getCurrentFileName():
    return session.get('file')

def saveNewFile(df = None, originalfilename = ''):
    log('Save the new file')
    log(df, originalfilename)
    data = Data(df, column_sort='idx',
        filename = re.sub('.csv', '', originalfilename),
        originalfilename = originalfilename)
    data.save()
    pass