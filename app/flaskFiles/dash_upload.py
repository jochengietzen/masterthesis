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
from flaskFiles.app import app, session

from jgietzen.Data import Data

from helper import *



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
                html.Div(rd[1], id='settings-div', style = {
                    'display': 'flex',
                    'justifyContent': 'space-between'
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

def renderData():
    log('Try to render the data block')
    data = Data.getCurrentFile()
    if type(data) == type(None):
        log('\tbut there is no data available\n----')
        colSortDiv = html.Div([html.Label('Timestamp column')])
        colIdDiv = html.Div([html.Label('Timeseries Id column')])
        colOutlierDiv = html.Div([html.Label('Outlier column')])
        return [[],[colSortDiv, colIdDiv, colOutlierDiv]]
    log('----')
    cols = data.bare_dataframe.columns.values
    colSort = dcc.Dropdown(id='dd-column-sort', value=data.column_sort, style = dropDownStyle)
    colSort.options=[{'label': 'Index', 'value': 'idx'},
                    *[{'label': key, 'value': key} for key in cols]]
    colSortDiv = html.Div([html.Label('Timestamp column'), colSort])

    colId = dcc.Dropdown(id='dd-column-id', value=data.column_id, style = dropDownStyle)
    colId.options=[{'label': 'None', 'value': 'None'},
                    *[{'label': key, 'value': key} for key in cols]]
    colIdDiv = html.Div([html.Label('Timeseries Id column'), colId])

    colOutlier = dcc.Dropdown(id='dd-column-outlier', value=data.column_outlier, style = dropDownStyle)
    colOutlier.options=[{'label': 'None', 'value': 'None'},
                    *[{'label': key, 'value': key} for key in cols]]
    colOutlierDiv = html.Div([html.Label('Outlier column'), colOutlier])

    return [
        html.Div([
            html.H5(data.originalfilename),
            dash_table.DataTable(
                data=data.bare_dataframe.head().to_dict('records'),
                columns=[{'name': i, 'id': i} for i in data.bare_dataframe.columns]
            ),
            html.Hr(),  # horizontal line
        ]),
        [
            colSortDiv,
            colIdDiv,
            colOutlierDiv
        ]
    ]


@app.callback([Output('output-data-upload', 'children'), Output('settings-div', 'children')],
            [
                Input('upload-data', 'contents'),
                Input('delete-data', 'n_clicks'),
                # Input('dd-column-sort', 'value'),
            ],
            [State('upload-data', 'filename'),
            State('upload-data', 'last_modified')])
def update_output(list_of_contents, n, list_of_names, list_of_dates):
    log('update data output with content:', type(list_of_contents))
    log('nclicks', n)
    # print(list_of_names, file=sys.stdout)
    # print(list_of_dates, file=sys.stdout)
    if n != None:
        log('Delete Button clicked')
        Data.deleteCurrentFile()
        return renderData()
    if list_of_contents is not None:
        children = parse_contents(list_of_contents, list_of_names, list_of_dates)
        return children
    return renderData()


@app.callback([Output('delete-data', 'disabled'), Output('delete-data-div', 'children')],
    [Input('output-data-upload', 'children')])
def renderDeleteButton(children):
    data = Data.getCurrentFile()
    log('button update disabled to', type(data) == type(None))
    deleteButton.style = [{'display': 'block'}, {'display': 'none'}][int(type(data) == type(None))]
    log(deleteButton)
    return [type(data) == type(None), [deleteButton]]


@app.callback(Output('hidden-div', 'children'), [
    Input('dd-column-sort', 'value'),
    Input('dd-column-id', 'value'),
    Input('dd-column-outlier', 'value'),
])
def updateData(sort, idd, outlier):
    log('Update data with')
    log(sort, idd, outlier)
    data = Data.getCurrentFile()
    if type(data) == type(None):
        return []
    if sort != None and sort != 'None':
        data.set_column_sort(sort)
    if idd != None and idd != 'None':
        data.set_column_id(idd)
    if outlier != None and outlier != 'None':
        data.column_outlier = outlier
    data.save()
    return []