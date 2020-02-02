import pandas as pd
import numpy as np
import pickle as pkl
from config import dir_datafiles
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go

from helper import valueOrAlternative, log, colormap, plotlyConf
from flaskFiles.app import session

class Data:
    __tsID = 'tsid'
    __tsTstmp = 'tststmp'
    __colOut = 'outlierColumns'
    __idIndex = None
    __kind = 'tskind'
    __sortCache = None
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
        self.raw_df = data.copy()
        self.raw_columns = self.raw_df.columns.tolist()
        self.frequency = valueOrAlternative(kwargs, 'frequency')
        self.short_desc = valueOrAlternative(kwargs, 'short_desc')
        self._column_id = valueOrAlternative(kwargs, 'column_id')
        self.windowsize = valueOrAlternative(kwargs, 'windowsize')
        assert has_timestamp != None and type(has_timestamp) == bool, 'Has Timestamp is required and needs to be of type boolean'
        self.has_timestamp = has_timestamp
        assert column_sort != None or self.frequency != None, 'Column sort is required and cannot be None if no frequency is available'
        self._column_sort = column_sort
        self.__kwargs = kwargs
        self.filename = valueOrAlternative(kwargs, 'filename', 'random')
        self.originalfilename = valueOrAlternative(kwargs, 'originalfilename')
        self._column_outlier = valueOrAlternative(kwargs, 'column_outlier')
        self._relevantColumns = valueOrAlternative(kwargs, 'relevant_columns')
        self.internalStore = {}

    def set_column_sort(self, column_sort):
        if self._column_sort == column_sort:
            return
        self._column_sort = column_sort

    def set_column_id(self, column_id):
        if self._column_id == column_id:
            return
        self._column_id = column_id
    
    def set_column_outlier(self, column_outlier):
        if self._column_outlier == column_outlier:
            return
        self._column_outlier = column_outlier

    def set_relevant_columns(self, relevant_columns):
        if self._relevantColumns == relevant_columns:
            return
        self._relevantColumns = relevant_columns
    
    @property
    def tsTstmp(self):
        return self.__tsTstmp

    @property
    def indexColumns(self):
        return [col for col in [self.column_sort, self.column_id] if col != None and col in self.raw_columns]
    
    @property
    def indexAndOutlierColumns(self):
        return [col for col in [self.column_sort, self.column_id, *self.column_outlier] if col != None and col in self.raw_columns]

    @property
    def relevant_columns_available(self):
        specialCols = self.indexAndOutlierColumns
        return [col for col in self.raw_columns if col not in specialCols]

    @property
    def outlier_columns_available(self):
        specialCols = self.indexColumns
        if self._relevantColumns != None and len(self._relevantColumns) > 0:
            specialCols += self.relevant_columns
        return [col for col in self.raw_columns if col not in specialCols]

    @property
    def sort_is_timestamp(self):
        return self.has_timestamp or self._column_sort == None and self.frequency != None
    
    @property
    def column_sort(self):
        if self._column_sort == 'idx':
            return self.__tsTstmp
        else:
            return self._column_sort if self._column_sort != None and self._column_sort in self.raw_columns else self.__tsTstmp
    
    @property
    def column_id(self):
        return self.__tsID if self._column_id == None or self._column_id not in self.raw_columns else self._column_id

    @property
    def column_outlier(self):
        return [col for col in (self._column_outlier if type(self._column_outlier) == list else [self._column_outlier]) if col in self.raw_columns] if type(self._column_outlier) in [list] else []
    
    @property
    def has_relevant_columns(self):
        return self._relevantColumns != None

    @property
    def relevant_columns(self):
        specialCols = self.indexAndOutlierColumns
        rel = [col for col in self._relevantColumns if col in self.raw_columns and col not in specialCols] if self._relevantColumns != None else self.raw_df.drop(columns=specialCols).columns.tolist()
        return rel
    
    @property
    def has_outlier(self):
        return len(self.column_outlier) > 0
    
    @property
    def outlier(self):
        dic = dict()
        for col in self.column_outlier:
            if col in self.raw_columns:
                dic[col] = self.raw_df[col].values.flatten()
        return dic
    
    @property
    def dataWithOutlier(self):
        df = self.data
        if self.has_outlier:
            column_outlier = self.column_outlier
            for col in column_outlier:
                df[col] = self.outlier[col]
        return df
    
    @property
    def data(self):
        df = pd.DataFrame()
        column_id = self.column_id
        df[column_id] = [0] * self.raw_df.shape[0] if column_id not in self.raw_columns else self.raw_df[[column_id]].values.flatten()
        column_sort = self.column_sort
        if column_sort == self.__tsTstmp:
            ids, counts = np.unique(df[column_id].values, return_counts=True)
            df[column_sort] = np.nan
            for idValue, count in zip(ids, counts):
                df.iloc[np.where(idValue == df[column_id])[0], np.where(column_sort == df.columns)[0]] = np.arange(0, count, 1) if self.frequency == None else np.arange(0, count/self.frequency, 1/self.frequency)
        else:
            df[column_sort] = self.raw_df[column_sort].values.flatten()
        relevant_columns = self.relevant_columns
        for col in relevant_columns:
            if col in self.raw_columns:
                df[col] = self.raw_df[col].values.flatten()
        return df
    

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
    
    # def plotdataTimeseries(self):
    #     data = self.data
    #     x = data[[self.column_sort]].values.flatten()
    #     ys = data[self.relevant_columns]
    #     ret = [{'x': x, 'name': col,
    #         'marker':{'color': colormap(ind)},
    #         'y': ys[[col]].values.flatten()} for ind, col in enumerate(ys.columns.tolist())]
    #     layout = dict(
    #         xaxis = dict(title = 'time' if self.has_timestamp == True else 'index'),
    #         yaxis = dict(title = 'value')
    #     )
    #     return ret, layout
    
    def plotdataTimeseriesGraph(self):
        return dcc.Graph(id='timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['style'],
                figure = self.plotdataTimeseriesFigure()
            )

    def plotdataTimeseriesFigure(self):
        data = self.data
        layout = dict(
            xaxis = dict(title = self.column_sort if self._column_sort != None else 'index'),
            hovermode = 'x'
            # yaxis = dict(title = 'value')
        )
        fig = go.Figure(**{'layout': dict(
                    title=dict(text='Timeseries data',
                    x = .5
                    ),
                    showlegend=True,
                    legend=dict(
                        x=1,
                        y=0
                    ),
                    **plotlyConf['layout'],
                    **layout,
                    margin=dict(l=40, r=0, t=40, b=30),
                )})
        for ind, col in enumerate(self.relevant_columns):
            fig.add_trace(go.Scatter(name=col , x=data[[self.column_sort]].values.flatten(), y=data[[col]].values.flatten(), marker= dict(color=colormap(ind))))
        return fig