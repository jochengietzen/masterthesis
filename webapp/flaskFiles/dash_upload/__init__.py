import base64
import datetime
import io
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State



import pandas as pd
import pickle
from webapp.flaskFiles.applicationProvider import app, session

from webapp.jgietzen.Data import Data

from webapp.helper import log

# Styles
from .styles \
    import *

# Components
from .components import *

def getUploadHTML():
    rd = renderData()
    return html.Div([
                uploadComponent,
                deleteButtonDiv,
                html.Hr(),
                html.Div(rd[1], id='settings-div', style = fullparentwidth),
                html.Div(rd[0], id='output-data-upload'),
                html.Div(id='hidden-div', style=displaynone)
            ])

def parse_contents(contents, filename, date):
    _, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    Data.saveCurrentFile(df, originalfilename=filename)
    return renderData()

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
    if data.has_timestamp:
        colFrequencyDiv.hidden = True
    colSortDiv.children = [colSortLabel, colSort, colIsTimestamp]
    colId.value = data.column_id
    colId.options=[{'label': 'None', 'value': 'Null'},
                    *[{'label': key, 'value': key} for key in cols]]
    colIdDiv.children = [colIdLabel, colId]
    colOutlier.options=[
        {'label': key, 'value': key} for key in data.outlier_columns_available
        ]
    colOutlierDiv.children = [colOutlierLabel, colOutlier]
    if data.has_outlier:
        colOutlier.value = data.column_outlier
    colRelevant.options=[
            {'label': key, 'value': key} for key in data.relevant_columns_available
        ]
    if data.has_relevant_columns:
        colRelevant.value = data.relevant_columns
    colRelevantDiv.children = [colRelevantLabel, colRelevant]
    return html.Div([
            colIdDiv,
            colSortDiv,
            colFrequencyDiv,
            colOutlierDiv,
            colRelevantDiv,
        ],style = settingsStyle)

def renderData():
    exists, data = Data.existsData()
    settings = renderSettings(data)
    if not exists:
        return [[],[]]
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
        Output('output-data-upload', 'children'), 
        Output('settings-div', 'children')
    ],
    [
        Input('upload-data', 'contents'),
        Input('delete-data', 'n_clicks'),
    ],
    [State('upload-data', 'filename'),
    State('upload-data', 'last_modified')])
def update_output(list_of_contents, n, list_of_names, list_of_dates):
    if n != None:
        Data.deleteCurrentFile()
        return renderData()
    if list_of_contents is not None:
        children = parse_contents(list_of_contents, list_of_names, list_of_dates)
        return children
    return renderData()


@app.callback([
        Output('delete-data', 'disabled'), 
        Output('delete-data-div', 'children'),
        Output('upload-data', 'disabled')
    ],
    [Input('output-data-upload', 'children')])
def renderDeleteButton(children):
    exists, _ = Data.existsData()
    deleteButton.style = [{'display': 'block'}, {'display': 'none'}][int(not exists)]
    return [not exists, [deleteButton], exists]


@app.callback( Output('input-frequency', 'value'),
[
    Input('clear-frequency', 'n_clicks'),
])
def clearFrequency(clear):
    exists, data = Data.existsData()
    if exists:
        if clear != None and clear != 'None':
            data.set_frequency(None)
        data.save()
        return data.frequency
    return None

@app.callback([
    Output('hidden-div', 'children'),
    Output('input-frequency-div', 'hidden')
    ], [
    Input('dd-column-sort', 'value'),
    Input('dd-column-id', 'value'),
    Input('dd-column-outlier', 'value'),
    Input('dd-columns-relevant', 'value'),
    Input('ri-is-timestamp', 'value'),
    Input('input-frequency', 'value'),
])
def updateData(sort, idd, outlier, relevant_columns, isTimestamp, frequency):
    ##log('Update data with')
    ##log(sort, idd, outlier)
    exists, data = Data.existsData()
    if not exists:
        return [[], True]
    if sort != None and sort != 'None':
        data.set_column_sort(sort)
    if idd != None and idd != 'None':
        data.set_column_id(idd)
    if outlier != None and outlier != 'None':
        data.set_column_outlier(outlier)
    if relevant_columns != None and relevant_columns != 'None':
        data.set_relevant_columns(relevant_columns)
    if isTimestamp != None and isTimestamp != 'None':
        data.set_has_timestamp_value(isTimestamp)
    if frequency != None and frequency != 'None':
        if not data.has_timestamp:
            data.set_frequency(frequency)
    data.save()
    hidden = data.has_timestamp
    return [[], hidden]