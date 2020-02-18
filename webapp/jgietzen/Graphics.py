from webapp.flaskFiles.DataHandler import existsData
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go


from webapp.helper import log

from webapp.config import percistency, plotlyConf,  colormap

def renderTimeseries():
    exists, data = existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            data.plotdataTimeseriesGraph()
        ]

def renderOutlierExplanation():
    exists, data = existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            html.Div(id='nowhere', hidden = True),
            data.plotoutlierExplanationPieChartsGraph(),
            data.plotOutlierDistributionGraph(),
            html.Div(data.contrastiveExplainOutlierBlock(blockIndex=1), id = 'contrastive-explain'),
            # data.matrixProfileGraph('isof')
        ]
