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
from webapp.flaskFiles.applicationProvider import dash, app, session
from ..DataHandler import *

from webapp.jgietzen.Data import Data

from webapp.helper import log

# Styles
from .styles \
    import *

# Components
from .components import *

def getUploadHTML():
    return html.Div([
                uploadComponent,
                html.Hr(),
                html.Div([
                    html.Div([html.H5(id='filename-h5'), 
                    saveButtonDiv], style = settingsStyle),
                    html.Hr(),
                    html.Div(id='upload-table'),
                ], id='output-data-upload'),
            ])

def parse_contents(contents, filename, date, returnDataframe = False):
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
    # saveNewFile(df, originalfilename=filename)
    if returnDataframe:
        return df, filename
    return [dash_table.DataTable(
                            data=df.head(20).to_dict('records'),
                            columns=[{'name': i, 'id': i} for i in df.columns.tolist()]
                        ), filename]



@app.callback(
    [Output('upload-table', 'children'),
    Output('filename-h5', 'children'),
    Output(ids['saveButtonDiv'], 'style')
    ],
    [Input('upload-data', 'contents'),
    saveButtonInputClick
    ],
    [State('upload-data', 'filename'), State('upload-data', 'last_modified')])
def update_output(list_of_contents, save_button_clicks, list_of_names, list_of_dates):
    log('hit')
    ctx = dash.callback_context
    triggered = []
    if not ctx.triggered:
        log('Not yet triggered')
        return [[], [], []]
    else:
        triggered = [trig['prop_id'].split('.')[0] for trig in ctx.triggered]
    if ids['saveButton'] in triggered:
        saveNewFile(*parse_contents(list_of_contents, list_of_names, list_of_dates, True))
    if list_of_contents is not None:
        children = parse_contents(list_of_contents, list_of_names, list_of_dates)
        return children + [{'display': 'block'}]
    return [[], [], []]


# @app.callback(
#     Output('upload-data', 'disabled'),
#     [Input('output-data-upload', 'children')])
# def renderDeleteButton(children):
#     exists, _ = existsData()
#     deleteButton.style = [{'display': 'block'}, {'display': 'none'}][int(not exists)]
#     return [exists]

