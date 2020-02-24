from .components import *
from webapp.flaskFiles.applicationProvider import app
import plotly.graph_objects as go
from time import sleep
from dash.dependencies import Input, Output, State
from webapp.flaskFiles.DataHandler import existsData
from webapp.helper import isNone, log
from dash import no_update as nu

updateTriggers = 2

def getExplanationHTML():
    exists, data = existsData()
    colOutlier.options=[{'label': 'None', 'value': 'None'}]
    colOutlier.options= colOutlier.options + [
        {'label': col, 'value': col} for col in data.column_outlier
    ] if exists else []
    colOutlier.value = 'None'
    fileOpened.children = f'{data.originalfilename}' if exists else []
    return [*updateTriggerDivs(updateTriggers), fileOpened, colOutlier, sliderOutlierblockDiv, matrixprofileGraph, explanationDiv]

@app.callback(
    [
        Output(ids['matrixprofileGraph'], 'figure'),
        Output(ids['explanationDiv'], 'children'),
        Output(ids['fileOpened'], 'children')
    ],
    updateTriggerInput([i+1 for i in range(updateTriggers)]),
    [State(ids['colOutlier'], 'value'), State(ids['sliderOutlierblock'], 'value')])
def updateMatrixProfile(*args):
    outcol = args[-2]
    blockindex = args[-1]
    if isNone(outcol):
        return [go.Figure(), [], []]
    exists, data = existsData()
    kwargs = {}
    if not isNone(outcol):
        kwargs['outcol'] = outcol
    if not isNone(blockindex):
        kwargs['blockindex'] = blockindex
    exists, data = existsData()
    fo = f'{data.originalfilename}' if exists else []
    if exists:
        return [data.matrixProfileFigure(**kwargs), data.contrastiveExplainOutlierBlock(**kwargs), fo]

@app.callback(
    [
    Output(ids['sliderOutlierblock'], 'value'),
    Output(ids['sliderOutlierblock'], 'max'),
    Output(ids['sliderOutlierblock'], 'marks'),
    updateTriggerOutput(1),
    ],
    [Input(ids['colOutlier'], 'value')])
def renderMPSettings(outcolumn):
    if isNone(outcolumn):
        return [0, 0, {}, []]
    exists, data = existsData()
    mv = data.getOutlierBlockLengths(outcolumn) if exists else 0
    return [0, mv, {i: str(i) for i in range(mv)}, []]

@app.callback(
    updateTriggerOutput(2),
    [Input(ids['sliderOutlierblock'], 'value')])
def updateSlider(val):
    if isNone(val):
        return nu
    return []