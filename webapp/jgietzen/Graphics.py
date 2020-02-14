from webapp.jgietzen.Data import Data
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go


from webapp.helper import log

from webapp.config import percistency, plotlyConf,  colormap



def renderTest():
    import dash_table
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        data.fitSurrogates()
        data.fitExplainers()
        _ = data.explainAll(0)
        slid = data.extract_features(windowsize=7, roll=False)
        return [
            html.Div([
            html.H5(data.originalfilename),
            dash_table.DataTable(
                data=slid.head(20).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in slid.columns]
            ),
            html.Hr(),  # horizontal line
            ])
        ]


def renderTimeseries():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            data.plotdataTimeseriesGraph()
        ]

def renderOutlierExplanation():
    exists, data = Data.existsData()
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

def maxValueMPSlider(outcolumn = 'None'):
    exists, data = Data.existsData()
    return data.getOutlierBlockLengths(outcolumn) if exists else 0

def renderSettingsButtons(outcolumn = 'None', block = 0):
    exists, data = Data.existsData()
    colOutlier = dcc.Dropdown(id='mp-column-outlier', value=outcolumn, style = {'minWidth': '100px'}, persistence = True)
    colOutlier.options=[{'label': 'None', 'value': 'None'}] + [
        {'label': col, 'value': col} for col in data.column_outlier
    ] if exists else []
    obl = maxValueMPSlider(outcolumn)
    sliderOutlierblock = dcc.Slider(id='mp-slider-outlierblock', value=block, min=0, max = obl if exists else 0, persistence = True)
    return [
        colOutlier,
        html.Div([html.Label('Outlier Nr.'),sliderOutlierblock])
    ]

def renderMatrixPlot():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        return [
            html.Div(renderSettingsButtons(),id='mp-settings'),
            data.matrixProfileGraph(),
            html.Div(
                html.Div(id='mp-contrastive-explanation-text'),
                id='mp-contrastive-explanation-div',
                style=dict(width='100%', backgroundColor='lightgrey')
            )
        ]