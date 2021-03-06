import math
import pandas as pd
import numpy as np
import dill as pkl
import tsfresh
import plotly_express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import colorlover as cl
import matrixprofile
from matrixprofile import matrixProfile

from webapp.config import dir_datafiles
from webapp.config import colormap, plotlyConf
from webapp.jgietzen.OutlierExplanation import OutlierExplanation
from webapp.jgietzen.Cachable import Cachable, cache
from webapp.jgietzen.Threading import threaded
from webapp.helper import valueOrAlternative, log, inspect, consecutiveDiff, slide_time_series, alternativeMap, castlist, isNone
from .HumanReadable import Explanation, Feature


class Data(Cachable):
    
    
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
        super().__init__(internalStore={},alwaysCheck= ['column_id', 'column_sort', 'relevant_columns', 'column_outlier'], verbose=True)
        self.__tsID = 'tsid'
        self.__tsTstmp = 'tststmp'
        self.__colOut = 'outlierColumns'
        self.__valueOfAnOutlier = 1
        self.__idIndex = None
        self.__kind = 'tskind'
        self.__sortCache = None
        self._frequency = None
        self.featureFrames = {}
        self.outlierExplanations = {}
        self.slidedData = {}
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
        self.filename = f"datafile_{valueOrAlternative(kwargs, 'filename', 'random')}"
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
                if col not in self.outlierExplanations:
                    self.initOutlierExplanation(col)

    def precalculate(self):
        self.initOutlierExplanations()
        for oek in self.outlierExplanations:
            oe = self.outlierExplanations[oek]
            log('Make featureframes for', oek)
            oe.makeFeatureFrames()
    
    def precalculatePlots(self):
        self.initOutlierExplanations()
        for oek in self.outlierExplanations:
            oe = self.outlierExplanations[oek]
            for bl, _ in enumerate(oe.outlierBlocks):
                self.matrixProfileFigure(outcol=oek, blockindex=bl)
                self.contrastiveExplainOutlierBlock(outcol=oek, blockindex=bl)

    
    def initOutlierExplanation(self, col):
        dat = self.dataWithOutlier
        assert col in dat.columns.tolist(), 'Column {col} not available'.format(col=col)
        outs = dat[[col]].values.flatten()
        outs = alternativeMap(outs, {1: True}, False)
        self.outlierExplanations[col] = OutlierExplanation(outs, self)
        return self.outlierExplanations[col]
    
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
                dic[col] = self.raw_df[col].values.flatten().astype(float).astype(int)
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
        settings = {
                'maximum':None,
                'minimum':None,
                'median': None,
                'mean': None,
                'length': None,
                }
        settings = Feature.explainableFeatures()
        return dict(
            column_id=self.column_id, column_sort=self.column_sort,
            # column_kind=self.column_id,
            default_fc_parameters=settings
        )

    @property
    def xAxisTitle(self):
        title = self.column_sort if self._column_sort != None else 'index'
        if self._has_timestamp:
            title += ' [sec]'
        return title

    def getRolledTimestamps(self, windowsize):
        return self.timestamps[windowsize // 2::windowsize]

    def reduceSlidedToRolled(self, slided, windowsize):
        tstmps = self.getRolledTimestamps(windowsize)
        return slided.loc[[i in tstmps for i in slided[[self.column_id]].values.flatten()], :]





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
        settings = self.extract_features_settings
        defset = settings['default_fc_parameters']
        sett = dict(f_agg='mean', lag = windowsize)
        for k in [key for key in list(defset.keys()) if callable(defset[key])]:
            settings['default_fc_parameters'][k] =\
                settings['default_fc_parameters'][k](sett)

        extracted = tsfresh.extract_features(slid, n_jobs= 0, **settings)
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

    @cache(payAttentionTo=['relevant_columns'])
    def get_feature_frame(self, windowsize, adjustedToOutlierBlock = False):
        if adjustedToOutlierBlock == True:
            # TODO
            raise NotImplementedError
        self.calc_feature_frame(windowsize)
        return self.featureFrames[windowsize]

    def fitSurrogates(self, adjustedToOutlierBlock = False):
        for oe in self.outlierExplanations:
            self.outlierExplanations[oe].fitSurrogate(seed = 1, adjustedToOutlierBlock = adjustedToOutlierBlock)

    def fitExplainers(self, adjustedToOutlierBlock = False):
        for oe in self.outlierExplanations:
            self.outlierExplanations[oe].fitExplainers(adjustedToOutlierBlock = adjustedToOutlierBlock)

    def explainAll(self, index = 0):
        a = []
        for oe in self.outlierExplanations:
            a += self.outlierExplanations[oe].explainAll(index)
        return a

    @cache()
    def contrastiveExplainOutlierBlock(self, outcol = None, blockindex = 0):
        self.fitSurrogates()
        self.fitExplainers()
        outcol = outcol if outcol != None else self.column_outlier[0]
        oe = self.outlierExplanations[outcol]
        blocks = oe.outlierBlocks
        bl, bchar = blocks[blockindex]
        exp = oe.explainContrastiveFoilInstance(instanceIndex = bl[0] + (bchar[1] // 2))
        humanreadable = Explanation.fromContrastiveResult(exp, oe.getDataframe(bchar[1]).columns.tolist(), oe.surrogates[bchar[1]].classes_)
        return humanreadable.explain()

    '''
    Save, load and delete functions
    '''
    @staticmethod
    def load(filename):
        if isNone(filename):
            return None
        from os.path import join, exists
        file = join(dir_datafiles, filename)
        if not exists(file):
            return None
        return pkl.load(open(file, 'rb'))

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

    









    '''
    Plotting with plotly functions
    '''
    
    # @cache()
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
            xaxis = dict(title = self.xAxisTitle),
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
            xaxis = dict(title = self.xAxisTitle),
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
        # if l == 1:
        #     cs = self.outlierExplanations[self.column_outlier[0]].getOutlierPartitions
        #     fig = go.Figure(go.Pie(labels=cs[2], values=cs[1], marker=dict(colors = cs[4])))
        # elif l > 1:
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
                b=10,
                t=10,
                pad=0
            ))
        return fig
        
    @cache(payAttentionTo=['column_outlier', 'relevant_columns'], ignore =['column_id', 'column_sort'] )
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


    def scatter(self, col=None, x = None, y = None, name = None):
        assert type(col) != type(None) or type(y) != type(None)
        if type(x) == type(None):
            x = self.timestamps
        if type(y) == type(None):
            y = self.data[castlist(col)].values.flatten()
        return go.Scatter(
            x = x,
            y = y,
            name= name if name != None else None
        )

    def matrixprofile(self, col, motiflen):
        mp = matrixProfile.stomp(self.data[castlist(col)].values.flatten(), motiflen)
        return self.scatter(y = mp[0], name = 'matrixprofile (len {})'.format(motiflen))

    def outlierShapes(self, relCol, outCol):
        self.recalculateOutlierExplanations()
        blocks = self.outlierExplanations[outCol].outlierBlocks
        def shape(x0, y0, x1, y1):
            return go.Scatter(
                x = [x0, x1, x1, x0, x0],
                y = [y0, y0, y1, y1, y0],
                fill = 'toself',
                marker = dict(opacity = 0),
                line = dict(color = 'rgb(255,0,0)')
            )
        tstmps = self.timestamps
        relData = self.data[castlist(relCol)].values
        xs = [
            dict(
                x0=tstmps[bl[0]],
                y0=np.min(relData[slice(*bl)]),
                x1=tstmps[bl[1]-1],
                y1=np.max(relData[slice(*bl)])
            ) for bl, bChar in blocks]
        return [shape(**x) for x in xs]

    # # @cache(payAttentionTo=['relevant_columns', 'column_outlier'])
    # def matrixProfileData(self, topExplanations = 3, thresholdLime = .05, topmotifs = 3):
    #     ret = dict()
    #     for outcol in self.column_outlier:
    #         curret = dict()
    #         oe = self.outlierExplanations[outcol]
    #         curret['outlierShapes'] = {rel: self.outlierShapes(rel, outcol) for rel in self.relevant_columns}

    #         ret[outcol] = curret   

    def getOutlierBlockLengths(self, outcolumn = None):
        self.recalculateOutlierExplanations()
        if outcolumn in [None, 'None']:
            return 0
        else:
            return len(self.outlierExplanations[outcolumn].outlierBlocks) - 1

    @cache()
    def matrixProfileFigure(self, outcol = None, blockindex = 0, topExplanations = 3, thresholdLime = .05, topmotifs = 3, traces_over_all = False):
        self.recalculateOutlierExplanations()
        outcol = outcol if outcol not in [None, 'None'] else self.column_outlier[0]
        oe = self.outlierExplanations[outcol]
        rows, cols = 3, 1
        specs = [[dict(rowspan = 1, colspan = cols)] for row in range(rows)]
        fig = make_subplots(rows, cols,
            specs = specs,
            print_grid=True,
            shared_xaxes=True,
            shared_yaxes=True,
            
        )
        outlierShapes = self.outlierShapes(self.relevant_columns, outcol)
        bl, bChar = oe.outlierBlocks[blockindex]
        outlierShape = outlierShapes[blockindex]
        currentBlockLength = bChar[1]
        outlierShape.line.color = 'rgba(255, 0, 0, .3)'
        outlierShape.name = 'outlier {}'.format(blockindex)
        # outlierShape.legendgroup = 'outlier {}'.format(blockindex)
        for relcol in self.relevant_columns:
            scat = self.scatter(relcol, name=relcol)
            mp = self.matrixprofile(col = relcol, motiflen = currentBlockLength)
            scat.legendgroup = '{}'.format(relcol)
            mp.legendgroup = '{}'.format(relcol)
            mp.marker.color = scat.marker.color
            fig.add_trace(scat, row = 1, col= 1)
            fig.add_trace(mp, row = 3, col = 1)
        fig.add_trace(outlierShape, row = 1, col = 1)
        explainedFeatures = oe.explainLimeInstance(instanceIndex = bl[0] + (bChar[1] // 2))
        explainedFeatures = explainedFeatures[1]
        explainedFeatures = explainedFeatures[:min(len(explainedFeatures),topExplanations)]
        df = oe.getDataframe(bChar[1])
        for ef in explainedFeatures:
            y = df[ef[0]]
            scat = self.scatter(y=y)
            scat.name = '{} ({:.3f})'.format(*ef)
            scat.legendgroup = 'outlier {}'.format(blockindex)
            if ef[1] <= thresholdLime:
                scat.visible = 'legendonly'
            fig.add_trace(scat, row = 2, col = 1)
        for rrow in list(reversed(range(1, rows))):
            row = 1 + rrow
            fig.update_xaxes(dict(title = self.xAxisTitle, matches='x{}'.format(row)), row=1, col=1)
            fig.update_xaxes(dict(title = self.xAxisTitle, matches='x'), row=row, col=1)
        # if traces_over_all:
        #     fig.update_traces(xaxis="x{}".format(rows))
        return fig
