import math
import pandas as pd
import numpy as np
import pickle as pkl
import tsfresh
from webapp.config import dir_datafiles
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import colorlover as cl

from webapp.config import colormap, plotlyConf
from webapp.flaskFiles.applicationProvider import session
from webapp.jgietzen.OutlierExplanation import OutlierExplanation
from webapp.jgietzen.Hashable import Hashable, cache
from webapp.jgietzen.Threading import threaded
from webapp.helper import valueOrAlternative, log, inspect, consecutiveDiff, slide_time_series, alternativeMap

class Data(Hashable):
    __tsID = 'tsid'
    __tsTstmp = 'tststmp'
    __colOut = 'outlierColumns'
    __valueOfAnOutlier = 1
    __idIndex = None
    __kind = 'tskind'
    __sortCache = None
    _frequency = None
    featureFrames = {}
    outlierExplanations = {}
    slidedData = {}
    
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
        super().__init__(alwaysCheck= ['column_id', 'column_sort', 'column_outlier'], verbose=True)
        self.raw_df = data.copy()
        self.raw_columns = self.raw_df.columns.tolist()
        self._frequency = valueOrAlternative(kwargs, 'frequency')
        self.short_desc = valueOrAlternative(kwargs, 'short_desc')
        self._column_id = valueOrAlternative(kwargs, 'column_id')
        assert has_timestamp != None and type(has_timestamp) == bool, 'Has Timestamp is required and needs to be of type boolean'
        self._has_timestamp = has_timestamp
        assert column_sort != None or self._frequency != None, 'Column sort is required and cannot be None if no frequency is available'
        self._column_sort = column_sort
        self.__kwargs = kwargs
        self.filename = valueOrAlternative(kwargs, 'filename', 'random')
        self.originalfilename = valueOrAlternative(kwargs, 'originalfilename')
        self._column_outlier = valueOrAlternative(kwargs, 'column_outlier')
        self._relevantColumns = valueOrAlternative(kwargs, 'relevant_columns')
        self.initOutlierExplanations()
        '''
        Possible Idea:
            - One could include the values available in outlier columns as dropdown to mark what is an outlier.
            For now we just assume that an outlier is marked with a 1
        '''

    def initOutlierExplanations(self):
        if len(self.column_outlier) > 0:
            for col in self.column_outlier:
                self.initOutlierExplanation(col)
    
    @threaded
    def initOutlierExplanation(self, col):
        dat = self.dataWithOutlier
        assert col in dat.columns.tolist(), 'Column {col} not available'.format(col=col)
        outs = dat[[col]].values.flatten()
        outs = alternativeMap(outs, {1: True}, False)
        self.outlierExplanations[col] = OutlierExplanation(outs, self)
    
    def recalculateOutlierExplanations(self):
        calculated = list(self.outlierExplanations.keys())
        outcols = self.column_outlier
        for toDelete in [col for col in calculated if col not in outcols]:
            del self.outlierExplanations[toDelete]
        calculated = list(self.outlierExplanations.keys())
        for toCalculate in [col for col in outcols if col not in calculated]:
            self.initOutlierExplanation(toCalculate)

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
        self.recalculateOutlierExplanations()

    def set_relevant_columns(self, relevant_columns):
        if self._relevantColumns == relevant_columns:
            return
        self._relevantColumns = relevant_columns
    
    def set_frequency(self, frequency):
        if self._frequency == frequency:
            return
        self._frequency = frequency

    def set_has_timestamp_value(self, has_timestamp):
        if type(has_timestamp) == str:
            has_timestamp = has_timestamp == 'True'
        if self._has_timestamp == has_timestamp:
            return
        if has_timestamp:
            self.set_frequency(None)
        self._has_timestamp = has_timestamp

    @property
    def has_timestamp_value(self):
        return self._has_timestamp

    @property
    def has_timestamp(self):
        return self._has_timestamp and self.column_sort in self.raw_df.columns

    @property
    def tsTstmp(self):
        return self.__tsTstmp
    
    @property
    def timestamps(self):
        if self.has_timestamp:
            return self.raw_df[[self.column_sort]].values.flatten()
        return self.data[[self.column_sort]].values.flatten()

    @property
    def ids(self):
        return self.data[[self.column_id]].values.flatten()

    @property
    def indexColumns(self):
        return [col for col in [self.column_id, self.column_sort] if col != None]
        # return [col for col in [self.column_sort, self.column_id] if col != None and col in self.raw_columns]
    
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
    def has_frequency(self):
        return self.frequency != None

    @property
    def frequency(self):
        if self._frequency != None:
            return self._frequency
        if self.has_timestamp:
            tmp = np.mean(np.ediff1d(self.timestamps))
            return 1/tmp if tmp != 0 else None
        return None

    @property
    def frequency_value(self):
        return self._frequency

    @property
    def sort_is_timestamp(self):
        return self.has_timestamp or self._column_sort == None and self._frequency != None
    
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
    
    @property
    def extract_features_settings(self):
        return dict(
            column_id=self.column_id, column_sort=self.column_sort,
            # column_kind=self.column_id,
            default_fc_parameters={'maximum':None, 'minimum':None}
        )

    def getRolledTimestamps(self, windowsize):
        return self.timestamps[windowsize // 2::windowsize]

    def reduceSlidedToRolled(self, slided, windowsize):
        tstmps = self.getRolledTimestamps(windowsize)
        return slided.loc[[i in tstmps for i in slided[[self.column_id]].values.flatten()], :]

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




    def slide(self, windowsize, cleanOut = False, **kwargs):
        assert len(np.unique(self.ids)) <= 1, 'Multiple Timelines Not yet supported'
        slid = slide_time_series(
            self.data,
            rolling_direction=1,
            max_timeshift=(windowsize),
            # max_timeshift=(windowsize-1),
            column_id = self.column_id,
            column_sort = self.column_sort,
            column_kind = self.column_id,
            **{k: kwargs[k] for k in kwargs.keys() if k in [k for k in tsfresh.utilities.dataframe_functions.roll_time_series.__code__.co_varnames]})
        if cleanOut:
            idx = self.timestamps[-(windowsize-1):]
            if len(idx) > 0:
                slid = slid.loc[[i not in idx for i in slid[self.column_id].values]]
        cols = [self.column_sort, self.column_id]
        cols = cols + [col for col in slid.columns.tolist() if col not in cols]
        slid = slid.reindex(columns=cols)
        slid.reset_index(drop=True, inplace=True)
        #slid[self.__kind] = np.repeat(np.arange(0,slid.shape[0]/windowsize, 1, int), windowsize)
        return slid

    @cache()
    def extract_features(self, windowsize, roll = False, removeNa=True):
        assert len(np.unique(self.ids)) <= 1, 'Multiple Timelines Not yet supported'
        slid = self.slide(windowsize)
        if roll:
            slid = self.reduceSlidedToRolled(slid, windowsize)
        extracted = tsfresh.extract_features(slid, n_jobs= 0, **self.extract_features_settings)
        extracted[self.column_sort] = extracted.index
        extracted[self.column_id] = 0
        extracted.reset_index(drop=True, inplace=True)
        extracted.sort_values(by=[self.column_id, self.column_sort], inplace = True)
        cols = self.indexColumns + [col for col in extracted.columns if col not in self.indexColumns]
        extracted = extracted[cols]
        if removeNa:
            extracted = extracted.loc[:,~extracted.isna().apply(any).values]
        return extracted


    '''
    Functions for Outlier explanations
    '''
    def calc_feature_frame(self, l):
        log('Feature frame calculation length', l)
        if l not in self.featureFrames:
            ret = self.extract_features(windowsize=l, roll = False, removeNa = True)
            # TODO: Investigate again, why you need the decrementation of -1
            self.featureFrames[l] = ret

    def get_feature_frame(self, l):
        self.calc_feature_frame(l)
        return self.featureFrames[l]



    '''
    Save and load functions
    '''
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
    









    '''
    Plotting with plotly functions
    '''
    @cache()
    def plotdataTimeseriesGraph(self):
        return dcc.Graph(id='timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['styles']['fullsize'],
                figure = self.plotdataTimeseriesOutlierGraph()
                # figure = self.plotdataTimeseriesFigure()
            )
    
    def plotdataTimeseriesOutlierGraph(self):
        rows, cols = 2, 1
        fig = make_subplots(rows=rows, cols=cols, specs=[[{"secondary_y": True}] for r in range(rows) for col in range(cols)])
        fig.layout = go.Layout(title=dict(text='Timeseries data with outliers', x = .5),
                                hovermode='x')
        ts = self.plotdataTimeseriesFigure()
        [fig.append_trace(ts.data[i], row=1, col = 1) for i in range(len(ts.data))]
        fig.update_layout(ts.layout)
        data = self.data[self.relevant_columns]
        mima = dict(minValue=data.min().min(), maxValue=data.max().max())
        outlierRectangles = self.plotdataOutlierBarsAsFigure(**mima)
        sums = self.dataWithOutlier[self.column_outlier].sum(axis=1)
        ticks = sums.max() if len(self.column_outlier) > 1 else 0
        ticks = list(range(ticks))
        [fig.add_trace(outlierRectangles.data[i], row=1, col = 1, secondary_y=True) for i in range(len(outlierRectangles.data))]
        fig.update_layout(outlierRectangles.layout)
        fig.update_yaxes(secondary_y=True, row=1, col=1, tickvals=ticks)
        # fig.update_yaxes(secondary_y=True, row=1, col=1)
        return fig

    @cache()
    def plotdataOutlierBarsAsFigure(self, minValue = -1, maxValue = -1):
        data = self.dataWithOutlier
        layout = dict(
            xaxis = dict(title = self.column_sort if self._column_sort != None else 'index'),
            hovermode = 'x'
        )
        layout = dict(
                    title=dict(text='Outlier Rectangles',
                    x = .5
                    ),
                    showlegend=True,
                    legend=dict(
                        x=1,
                        y=0,
                        bgcolor = 'rgba(0,0,0,0)'
                    ),
                    **plotlyConf['layout'],
                    **layout,
                    margin=dict(l=40, r=0, t=40, b=30),
                    barmode='stack',
                    yaxis = dict(
                        side = 'left',
                        ticks= "", 
                        # autotick= True, 
                        showgrid= False, 
                        showline= True, 
                        zeroline= False, 
                        autorange= True, 
                        showticklabels= True
                    ),
                    yaxis2 = dict(
                        side='right',
                        ticks= "outside",
                        rangemode = 'normal',
                        autorange = True,
                        # autotick= True, 
                        # showgrid= False, 
                        showline= False, 
                        zeroline= True, 
                        overlaying= "y"
                    )
                )
        fig = go.Figure(**{'layout': layout})
        x = data[[self.column_sort]].values.flatten()
        scales = [
            cl.scales[key]['seq']['Reds'] for key in cl.scales if len(cl.scales[key]['seq']) > 0
            ]
        cm = scales[np.argmin([abs(len(s) - len(self.column_outlier)) for s in scales])]
        for ind, col in enumerate(self.column_outlier):
            current = data[[col]].values.flatten()
            color = cm[ind % len(cm)]
            colora = color.replace('rgb','rgba').replace(')', ',.4)')
            fig.add_trace(go.Bar(
                name=col,
                x=x[np.where(current != 0)[0]],
                y=current[np.where(current != 0)[0]],
                marker=dict(
                    line=dict(
                        color=colora,
                        width=2
                    ),
                    color=colora
                ),
                yaxis='y2'
            ))
        fig.update_shapes(dict(xref='x', yref='y'))
        return fig

    @cache(payAttentionTo=['relevant_columns'])
    def plotdataTimeseriesFigure(self):
        data = self.data
        layout = dict(
            xaxis = dict(title = self.column_sort if self._column_sort != None else 'index'),
            hovermode = 'x'
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

    def plotoutlierExplanationPieChartsFigure(self, breakAfterXCharts = 5):
        self.recalculateOutlierExplanations()
        l = len(self.column_outlier)
        fig = None
        if l == 1:
            cs = self.outlierExplanations[self.column_outlier[0]].getOutlierPartitions
            fig = go.Figure(go.Pie(labels=cs[2], values=cs[1], marker=dict(colors = cs[4])))
        elif l > 1:
            rows, cols = 1, l
            l2 = l/2 if l > breakAfterXCharts else l
            if l > breakAfterXCharts:
                rows, cols = 2, math.ceil(l2)
            fig = make_subplots(rows, cols,
                    print_grid=True,
                    specs=[[{"type": 'domain'} for col in range(cols)] for r in range(rows)]
                )
            row, column = 1, 0
            for _, col in enumerate(self.column_outlier):
                column += 1
                if column > l2:
                    row +=1
                    column = 1
                cs = self.outlierExplanations[col].getOutlierPartitions
                fig.add_trace(go.Pie(
                    title=dict(text=col, position='bottom center'),
                    showlegend=False,
                    values=cs[1],
                    name=col,
                    marker=dict(colors=cs[4]),
                    labels = ['{} {}'.format(col, c) for c in cs[2]],
                ), row, column)
            fig.update_layout(
                margin=go.layout.Margin(
                    l=0,
                    r=0,
                    b=0,
                    t=0,
                    pad=0
                ))
        return fig
        
    @cache(payAttentionTo=['column_outlier'], ignore =['column_id', 'column_sort'] )
    def plotoutlierExplanationPieChartsGraph(self):
        return dcc.Graph(id='timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['styles']['smallCorner'],
                figure = self.plotoutlierExplanationPieChartsFigure()
            )
    
    @cache(payAttentionTo=['column_outlier', 'relevant_columns'], ignore =['column_id', 'column_sort'] )
    def plotOutlierDistributionGraph(self, shareX = True):
        return dcc.Graph(id='timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['styles']['supersize'],
                figure = self.plotOutlierDistributionFigure()
            )

    def plotOutlierDistributionFigure(self, shareX = True):
        self.recalculateOutlierExplanations()
        rows, cols = len(self.relevant_columns), len(self.column_outlier)
        fig = make_subplots(
            rows=rows,
            cols=cols,
            print_grid=True,
            shared_xaxes= shareX,
            shared_yaxes=True,
            start_cell='top-left',
            horizontal_spacing=.05,
            vertical_spacing = .2,
            subplot_titles= ['{out} for variable {col}'.format(out=out, col=col) for col in self.relevant_columns for out in self.column_outlier]
            )
        fig.update_layout(dict(title=dict(text='Distribution of outliers vs inliers', x = .5), hovermode = 'x'))
        
        data = self.data
        for ind, col in enumerate(self.relevant_columns):
            y = data[[col]].values.flatten()
            row = 1 + ind
            for ind2, out in enumerate(self.column_outlier):
                groups = {}
                groupCount = {}
                currentrow = row
                for _, (block, bchar, bcolor) in enumerate(self.outlierExplanations[out].consecBlocksForPlotting):
                    if bchar[0] not in groupCount:
                        groupCount[bchar[0]] = 0
                    y0 = y[block[0]:block[1]]
                    name = '{}-{}-{}'.format(bchar[0], col, groupCount[bchar[0]])
                    name = '{}-{}'.format(bchar[0], groupCount[bchar[0]]) if shareX else name
                    fig.add_trace(go.Box(y=y0,
                        legendgroup = '{}-{}'.format(bchar[0], col),
                        name = name,
                        showlegend=False,
                        marker_color=bcolor,
                        boxpoints='suspectedoutliers',
                    ), currentrow, 1 + ind2)
                    groupCount[bchar[0]] += 1
                    if bchar[0] not in groups:
                        groups[bchar[0]] = bcolor
            [fig.add_trace(go.Box(y = ['null'],legendgroup= '{}-{}'.format(c[0], col),name = '{}-{}'.format(c[0], col), marker_color = c[1]), currentrow, 1) for c in groups.items()]
        for yaxis in [ya for ya in inspect(fig.layout) if ya.startswith('axis', 1)]:
            getattr(fig.layout, yaxis).showticklabels = True
        return fig