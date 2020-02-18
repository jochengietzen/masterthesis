import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from webapp.helper import castlist
from webapp.config import plotlyConf
from .styles import *
ids = dict(
    matrixprofileGraph = 'matrixprofile-timeseries-graph',
    colOutlier = 'mp-column-outlier',
    sliderOutlierblock = 'mp-slider-outlierblock',
    explanationText = 'mp-contrastive-explanation-div',
    explanationDiv = 'mp-contrastive-explanation-text',
    )

updateTriggerDivs = lambda x: [html.Div(id=f'update-explanation-trigger-{i + 1}', style=displaynone) for i in range(x)]
updateTriggerOutput = lambda index: Output(f'update-explanation-trigger-{index}', 'children')
updateTriggerInput = lambda indexes: [Input(f'update-explanation-trigger-{i}', 'children') for i in castlist(indexes)]

matrixprofileGraph = dcc.Loading(dcc.Graph(id=ids['matrixprofileGraph'],
                config = plotlyConf['config'],
                style= plotlyConf['lambdastyles']['fullsize'](3, 200),
            ))
explanationDiv = dcc.Loading(html.Div(
                html.Div(id=ids['explanationText']),
                id=ids['explanationDiv'],
                style=explanationDivStyle
            ))


colOutlier = dcc.Dropdown(id=ids['colOutlier'], value='None', style = {'minWidth': '100px'}, persistence = True)
sliderOutlierblock = dcc.Slider(id=ids['sliderOutlierblock'], value=0, min=0, max = 0, persistence = True)
sliderOutlierblockDiv = html.Div([html.Label('Outlier Nr.'), sliderOutlierblock])