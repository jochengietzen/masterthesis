import base64
import datetime
import io
import sys

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table


import pandas as pd
import pickle
from webapp.flaskFiles.applicationProvider import app, session

from webapp.jgietzen.Data import Data

from webapp.helper import log



deleteButton = html.Button('Delete data',id='delete-data')
dropDownStyle = {
    'minWidth': '100px'
}

# colSort = dcc.Dropdown(id='dd-column-sort', value='idx', style = dropDownStyle)
# colSortDiv = html.Div([html.Label('Timestamp column'), colSort])

def getUploadHTML():
    # print(renderData(), file=sys.stdout)
    rd = renderData()
    return html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    }
                ),
                html.Div(deleteButton, id='delete-data-div', style={
                    'display': 'flex',
                    'justifyContent': 'flex-end'
                }),
                html.Hr(),
                html.Div(rd[1], id='settings-div', style = {
                    # 'display': 'flex',
                    # 'justifyContent': 'space-around'
                    'width': '100%'
                }),
                html.Div(rd[0], id='output-data-upload'),
                html.Div(id='hidden-div', style={'display': 'none'})
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
    colIdDiv = html.Div([html.Label('Timeseries Id column')])
    colSortDiv = html.Div([html.Label('Timestamp column')])
    colFrequencyDiv = html.Div([html.Label('Frequency of data')], id = 'input-frequency-div')
    colOutlierDiv = html.Div([html.Label('Outlier column')])
    colRelevantDiv = html.Div([html.Label('Relevant columns to take a look at')])
    saveResultsDiv = html.Div([html.Label('Show updates')], id='refresh-button')
    if type(data) == type(None):
        return [colSortDiv, colIdDiv, colOutlierDiv, colRelevantDiv]
    saveResults = html.A('Refresh', href='/')
    saveResultsDiv.children = saveResultsDiv.children + [saveResults]
    cols = data.raw_columns
    colSort = dcc.Dropdown(id='dd-column-sort', value=data.column_sort, style = dropDownStyle)
    colSort.options=[{'label': 'Index', 'value': data.tsTstmp},
                    *[{'label': key, 'value': key} for key in cols]]
    colIsTimestamp = dcc.RadioItems(id='ri-is-timestamp',
    options=[
        dict(label='Is Timestamp in [s]', value='True'),
        dict(label='Not a Timestamp', value='False')
    ], value = str(data.has_timestamp_value))

    colFrequency = dcc.Input(id='input-frequency',
                            type='number',
                            placeholder=1000,
                            value = data.frequency_value
                            )
    buttonClearFrequency = html.Button('Clear Frequency', id='clear-frequency')
    colFrequencyDiv.children = colFrequencyDiv.children + [colFrequency, buttonClearFrequency]
    for child in colFrequencyDiv.children:
        child.style = dict(width='100%')
    colFrequencyDiv.style = dict(
        maxWidth = '200px',
    )
    if data.has_timestamp:
        colFrequencyDiv.hidden = True

    colSortDiv.children = colSortDiv.children + [colSort, colIsTimestamp]

    colId = dcc.Dropdown(id='dd-column-id', value=data.column_id, style = dropDownStyle)
    colId.options=[
                    {'label': 'None', 'value': 'Null'},
                    *[{'label': key, 'value': key} for key in cols]]
    colIdDiv.children = colIdDiv.children + [colId]

    colOutlier = dcc.Dropdown(id='dd-column-outlier', multi=True, style = dropDownStyle)
    colOutlier.options=[
        {'label': key, 'value': key} for key in data.outlier_columns_available
        ]
    colOutlierDiv.children = colOutlierDiv.children + [colOutlier]
    if data.has_outlier:
        colOutlier.value = data.column_outlier
    colRelevant = dcc.Dropdown(
        id = 'dd-columns-relevant',
        style = dropDownStyle,
        multi=True,
    )  
    colRelevant.options=[
            {'label': key, 'value': key} for key in data.relevant_columns_available
        ]
    if data.has_relevant_columns:
        colRelevant.value = data.relevant_columns
    colRelevantDiv.children = colRelevantDiv.children + [colRelevant]
    return html.Div([
            colIdDiv,
            colSortDiv,
            colFrequencyDiv,
            colOutlierDiv,
            colRelevantDiv,
            # saveResultsDiv
        ],style = dict(width='100%', display='flex', justifyContent='space-around'))

def renderData():
    data = Data.getCurrentFile()
    settings = renderSettings(data)
    if type(data) == type(None):
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
    data = Data.getCurrentFile()
    ##log('button update disabled to', type(data) == type(None))
    deleteButton.style = [{'display': 'block'}, {'display': 'none'}][int(type(data) == type(None))]
    ##log(deleteButton)
    return [type(data) == type(None), [deleteButton], type(data) != type(None)]


@app.callback( Output('input-frequency', 'value'),
[
    Input('clear-frequency', 'n_clicks'),
])
def clearFrequency(clear):
    data = Data.getCurrentFile()
    if type(data) != type(None):
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