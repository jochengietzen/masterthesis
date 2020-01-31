import pandas as pd
import numpy as np
import pickle as pkl
from config import dir_datafiles

from helper import valueOrAlternative
from flaskFiles.app import session

class Data:
    __tsID = 'tsid'
    __tsTstmp = 'tststmp'
    __idIndex = None
    __kind = 'tskind'
    internalStore = {}
    
    def __init__(self, data, column_sort = 'idx', has_timestamp = False, **kwargs):
        '''
        Initialization of this Object
            - data: the dataframe of a timeseries as pandas df
            - column_sort: indicates to the column, that orders the data. Optimal case this is a timestamp
            - has_timestamp: boolean, that points out, whether the column_sort is a timestamp or not
            - frequency: (partly optional) frequency in Hz by which the data is sampled
                        if data has a real timestamp column, frequency can be calculated by that
            - short_desc: short description which could be shown in a column
            - column_id: indicates the column, which differentiates between multiple timeseries in a dataset
                        This will also be used to distinguish between uni- and multivariate data
            - label_column
        '''
        self.bare_dataframe = data.copy()
        self.frequency = valueOrAlternative(kwargs, 'frequency')
        self.short_desc = valueOrAlternative(kwargs, 'short_desc')
        self.column_id = valueOrAlternative(kwargs, 'column_id')
        self.windowsize = valueOrAlternative(kwargs, 'windowsize')
        assert column_sort != None, 'Column sort is required and cannot be None'
        self.column_sort = column_sort
        assert has_timestamp != None and type(has_timestamp) == bool, 'Has Timestamp is required and needs to be of type boolean'
        self.has_timestamp = has_timestamp
        self.__kwargs = kwargs
        self.__initialize()
        self.filename = valueOrAlternative(kwargs, 'filename', 'random')
        self.originalfilename = valueOrAlternative(kwargs, 'originalfilename')
        self.column_outlier = valueOrAlternative(kwargs, 'column_outlier')
        self.internalStore = {}
        #print(inspectTuple(self))
        #print(self.bare_dataframe)


    def set_column_sort(self, column_sort):
        if self.column_sort == column_sort:
            return
        self.bare_dataframe = self.bare_dataframe.drop(columns=[self.column_sort])
        self.column_sort = column_sort
        self.__initialize()

    def set_column_id(self, column_id):
        if self.column_id == column_id:
            return
        self.bare_dataframe = self.bare_dataframe.drop(columns=[self.column_id])
        self.column_id = column_id
        self.__initialize()

    def __initialize(self):
        if self.column_id == None:
            self.bare_dataframe[self.__tsID] = [0] * self.bare_dataframe.shape[0]
            self.column_id = self.__tsID
        else:
            self.__tsID = self.column_id
        tmpBool = False
        if not self.has_timestamp and self.frequency != None and self.column_sort != 'idx':
            self.bare_dataframe.drop(columns=[self.column_sort], inplace=True)
            tmpBool = True
        if self.column_sort == 'idx' or tmpBool:
            self.column_sort = self.__tsTstmp if not tmpBool else self.column_sort
            self.__tsTstmp = self.column_sort if tmpBool else self.__tsTstmp
            #_mpTMP = 'temporaryTimeColumnSave' + ''.join(np.array(np.random.randint(0, 10, 10), str))
            #self.bare_dataframe.rename(columns={'time': _mpTMP}, inplace=True)
            ids, counts = np.unique(self.bare_dataframe[self.column_id].values, return_counts=True)
            self.bare_dataframe[self.column_sort] = np.nan
            for idValue, count in zip(ids, counts):
                #print(self.bare_dataframe.loc[np.where(idValue == self.bare_dataframe[self.column_id])][[self.__tsTstmp]])
                #print(np.arange(0, count, 1) if self.frequency == None else np.arange(0, count/self.frequency, 1/self.frequency))
                self.bare_dataframe.iloc[np.where(idValue == self.bare_dataframe[self.column_id])[0], np.where(self.column_sort == self.bare_dataframe.columns)[0]] = np.arange(0, count, 1) if self.frequency == None else np.arange(0, count/self.frequency, 1/self.frequency)
        else: 
            self.__tsTstmp = self.column_sort
        self.__reorderData()
    
    def __reorderData(self):
        idxes = [self.column_id, self.column_sort]
        cols = idxes + [x for x in self.bare_dataframe.columns.tolist() if x not in idxes]
        self.bare_dataframe = self.bare_dataframe.reindex(columns=cols)


    @property
    def outlier(self):
        return self.bare_dataframe[[self.column_outlier]] if self.column_outlier != None else None


    def save(self):
        from os.path import join
        pkl.dump(self, open(join(dir_datafiles, self.filename), 'wb'))
    
    def delete(self):
        from os.path import join, exists
        from os import remove
        file = join(dir_datafiles, self.filename)
        if exists(file):
            remove(file)
        del self

    def plotdataTimeseries(self):
        x = self.bare_dataframe[[self.column_sort]].values.flatten()
        ys = self.bare_dataframe.drop(columns=[self.column_sort, self.column_id, self.column_outlier])
        ret = [{'x': x, 'name': col,
            'marker':{'color':'rgb(55, 83, 109)'},
            'y': ys[[col]].values.flatten()} for col in ys.columns.tolist()]
        print(ret)
        layout = dict(
            xaxis = dict(title = 'time' if self.has_timestamp == True else 'index'),
            yaxis = dict(title = 'value')
        )
        return ret, layout

    @staticmethod
    def load(filename):
        from os.path import join, exists
        file = join(dir_datafiles, filename)
        if not exists(file):
            return None
        return pkl.load(open(file, 'rb'))

    @staticmethod
    def getCurrentFile():
        data = Data.load(session.get('uid'))
        if type(data) == type(None):
            # log('No data file available yet')
            return None
        return data
    
    @staticmethod
    def existsData():
        data = Data.getCurrentFile()
        return data != None, data
    
    @staticmethod
    def existsCurrentFile():
        from os.path import join, exists
        return exists(join(dir_datafiles, session.get('uid')))

    @staticmethod
    def saveCurrentFile(df = None, originalfilename = None, column_sort = 'idx', column_id = None, column_outlier = None):
        data = Data.getCurrentFile()
        if type(data) == type(None):
            data = Data(df, column_sort=column_sort, 
                column_id = column_id, column_outlier = column_outlier,
                filename = session.get('uid'),
                originalfilename = originalfilename)
            data.save()
        else:
            data.bare_dataframe = df if type(df) != type(None) else data.bare_dataframe
            data.originalfilename = df if type(originalfilename) != type(None) else data.originalfilename
            data.column_id = column_id if column_id != None else data.column_id
            data.column_sort = column_sort if column_sort != None else data.column_sort
            data.column_outlier = column_outlier if column_outlier != None else data.column_outlier
            data.save()
    
    @staticmethod
    def deleteCurrentFile():
        data = Data.getCurrentFile()
        if type(data) != type(None):
            data.delete()
