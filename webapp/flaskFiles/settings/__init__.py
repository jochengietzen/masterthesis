import base64
import datetime
import io
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dash import no_update as nu
import dash_table
from dash.dependencies import Input, Output, State



import pandas as pd
import pickle
from webapp.flaskFiles.applicationProvider import app, session
from ..DataHandler import *
from ..sessionHandling import setFile

from webapp.flaskFiles.DataHandler import *

from webapp.helper import log, isNone

# Styles
from .styles \
    import *

# Components
from .components import *

'''
TODO:
- Liste mit zur Verfügung stehenden Dateien
- Ausgewählte Datei muss in der Session getrackt werden
- Settings für die ausgewählte Datei rendern
- Am Besten alles schon vorher erzeugen und dann mit displaynone verbergen,
dann sind die Callbacks auch nicht kaputt

'''

updateTriggers = 4

def getSettingsHTML():
    rd = renderData()
    dataChoice.options = \
            getAvailableDataSetsAsOptionList()
    dataChoice.value = getCurrentFileName()
    return html.Div([
                html.Hr(),
                dataChoiceDiv,
                html.Hr(),
                html.Div(rd[1], id='settings-div', style = fullparentwidth),
                saveButtonDiv,
                html.Hr(),
                deleteButtonDiv,
                html.Div(rd[0], id='output-data-preview'),
                *updateTriggerDivs(updateTriggers)
            ])

def renderSettings(data = None):
    if type(data) == type(None):
        return [colSortDiv, colIdDiv, colOutlierDiv, colRelevantDiv]
    cols = data.raw_columns
    colSort.value = data.column_sort
    colSort.options=[{'label': 'Index', 'value': data.tsTstmp},
                    *[{'label': key, 'value': key} for key in cols]]
    colIsTimestamp.value = str(data.has_timestamp_value)
    colFrequency.value = data.frequency_value
    for child in colFrequencyDiv.children:
        child.style = dict(width='100%')
    colFrequencyDiv.hidden = data.has_timestamp
    
    colSortDiv.children = [colSortLabel, colSort, colIsTimestamp]
    colId.value = data.column_id
    colId.options=[{'label': 'None', 'value': 'Null'},
                    *[{'label': key, 'value': key} for key in cols]]
    colIdDiv.children = [colIdLabel, colId]
    colOutlier.options=[
        {'label': key, 'value': key} for key in data.outlier_columns_available
        ]
    colOutlierDiv.children = [colOutlierLabel, colOutlier]
    colOutlier.value = data.column_outlier
    colRelevant.options=[
            {'label': key, 'value': key} for key in data.relevant_columns_available
        ]
    if data.has_relevant_columns:
        colRelevant.value = data.relevant_columns
    else:
        colRelevant.value = []
    colRelevantDiv.children = [colRelevantLabel, colRelevant]
    return html.Div([
            colIdDiv,
            colSortDiv,
            colFrequencyDiv,
            colOutlierDiv,
            colRelevantDiv,
        ],style = settingsStyle)

def renderData():
    exists, data = existsData()
    settings = renderSettings(data)
    if not exists:
        return [[], []]
    tableData = data.dataWithOutlier
    return [
        html.Div([
            html.H5(data.originalfilename),
            html.H5(data.frequency),
            dash_table.DataTable(
                data=tableData.head(20).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in tableData.columns]
            ),
            html.Hr(),  # horizontal line
        ]),
        settings
    ]

@app.callback(
    [
        Output('output-data-preview', 'children'),
        Output('settings-div', 'children'),
        Output(ids['dataChoice'], 'options')
    ],
    updateTriggerInput([i+1 for i in range(updateTriggers)])
)
def renderPreview(*args):
    return [*renderData(), getAvailableDataSetsAsOptionList()]


def clearOptions():
    colId.options = []
    colId.value = None
    colSort.options = []
    colSort.value = None
    colOutlier.options = []
    colOutlier.value = None
    colRelevant.options = []
    colRelevant.value = None


@app.callback(
    updateTriggerOutput(1),
    [Input(ids['dataChoice'], 'value')]
)
def setFileChoice(filechoice):
    log('setFileChoice triggered')
    if isNone(filechoice):
        return []
    setFile(filechoice)
    # clearOptions()
    return []


@app.callback(
    updateTriggerOutput(2),
    [Input(ids['saveButton'], 'n_clicks')],
    [State(o, 'value') for o in [
        'dd-column-sort',
        'dd-column-id',
        'dd-column-outlier',
        'dd-columns-relevant',
        'ri-is-timestamp',
        'input-frequency',
    ]]
)
def saveSettings(_, *args):
    log('saveSettings triggered')
    exists, data = existsData()
    log('Save triggered')
    if not exists:
        return []
    for ind, commands in enumerate([
            data.set_column_sort,
            data.set_column_id,
            data.set_column_outlier,
            data.set_relevant_columns,
            data.set_has_timestamp_value,
            data.set_frequency,
        ]):
        commands(args[ind])
    data.save()
    return []

@app.callback(
    updateTriggerOutput(3),
    [Input(ids['clearFrequency'], 'n_clicks')],
)
def clearFrequency(clear):
    log('clearFrequency triggered')
    exists, data = existsData()
    if exists:
        data.set_frequency(None)
        data.save()
    return []
    
@app.callback(
    [
        updateTriggerOutput(4),
        Output(ids['dataChoice'], 'value')
    ],
    [Input(ids['deleteButton'], 'n_clicks')],
)
def deleteFile(_):
    log('deleteFile triggered')
    deleteCurrentFile()
    return [[], None]


@app.callback(
    Output(ids['precalculateLoader'], 'children'),
    [Input(ids['precalculateButton'], 'n_clicks')]
)
def precalculate(_):
    exists, data = existsData()
    if not exists:
        return []
    data.precalculate()
    data.save()
    return []