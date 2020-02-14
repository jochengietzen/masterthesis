from dash.dependencies import Input, Output

from webapp.flaskFiles.applicationProvider import app, server, session
from webapp.flaskFiles.dash_upload import getUploadHTML
import uuid
from datetime import timedelta

import sys
from webapp.helper import log
from webapp.config import dir_sessions
import json

from webapp.jgietzen.Data import Data
from webapp.jgietzen.Graphics import renderTimeseries, renderTest, renderOutlierExplanation, renderMatrixPlot, renderSettingsButtons, maxValueMPSlider


@app.server.before_first_request
def sessionPermanent():
    session.permanent = True
    server.permanent_session_lifetime = timedelta(weeks=4)

@app.server.before_request
def uid():
    session['uid'] = '8a99f029-79d8-4ded-b2f3-262a98cb383c'
    if 'uid' not in session:
        log(session)
        session['uid'] = '8a99f029-79d8-4ded-b2f3-262a98cb383c'
        # session['uid'] = uuid.uuid4().__str__()

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_tab(tab):
    if tab == 'tab-1':
        return getUploadHTML()
    elif tab == 'tab-2':
        return renderTimeseries()
    elif tab == 'tab-3':
        return renderOutlierExplanation()
    elif tab == 'tab-4':
        return renderMatrixPlot()

@app.callback(
    [Output('mp-slider-outlierblock', 'max'),
    Output('mp-slider-outlierblock', 'marks')],
    [   Input('mp-column-outlier', 'value')]
)
def renderMPSettings(outcol):
    mv = maxValueMPSlider(outcolumn=outcol)
    return [mv, {i: str(i) for i in range(mv)}]

@app.callback(
        Output('mp-slider-outlierblock', 'value'),
        [Input('mp-column-outlier', 'value')],
)
def resetSlider(col):
    return 0

@app.callback(
    Output('matrixprofile-timeseries-graph', 'figure'),
    [
        Input('mp-column-outlier', 'value'),
        Input('mp-slider-outlierblock', 'value'),
    ]
)
def renderMPGraph(outcol, block):
    kwargs = {}
    none = [None, 'None']
    exists, data = Data.existsData()
    if outcol not in none:
        kwargs['outcol'] = outcol
    if block not in none:
        kwargs['blockindex'] = block
    if exists:
        return data.matrixProfileFigure(**kwargs)
    return None

@app.callback(
    Output('mp-contrastive-explanation-text', 'children'),
    [
        Input('mp-column-outlier', 'value'),
        Input('mp-slider-outlierblock', 'value'),
    ]
)
def renderMatrixProfileText(outcol, block):
    kwargs = {}
    none = [None, 'None']
    exists, data = Data.existsData()
    if outcol not in none:
        kwargs['outcol'] = outcol
    if block not in none:
        kwargs['blockindex'] = block
    if exists:
        return data.contrastiveExplainOutlierBlock(**kwargs)
    return None

# @app.callback(
#     Output('nowhere', 'children'),
#     [Input('matrixprofile-timeseries-graph', 'hoverData')])
# def display_hover_data(hoverData):
#     log(json.dumps(hoverData, indent=2))
#     return []

# @app.server.route('/visits-counter/')
# def visits():
#     if 'visits' in session:
#         session['visits'] = session.get('visits') + 1  # reading and updating session data
#     else:
#         session['visits'] = 1 # setting session data
#     return "Total visits: {}".format(session.get('visits'))
 
# @app.server.route('/delete-visits/')
# def delete_visits():
#     session.pop('visits', None) # delete visits
#     return 'Visits deleted'
        