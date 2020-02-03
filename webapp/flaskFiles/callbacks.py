from dash.dependencies import Input, Output

from webapp.flaskFiles.applicationProvider import app, session
from webapp.flaskFiles.dash_upload import getUploadHTML
import uuid

import sys
from webapp.helper import log

from webapp.jgietzen.Graphics import renderTimeseries, renderTest

@app.server.before_request
def uid():
    if 'uid' not in session:
        log(session)
        session['uid'] = uuid.uuid4().__str__()

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_tab(tab):
    if tab == 'tab-1':
        return getUploadHTML()
    elif tab == 'tab-2':
        return renderTimeseries()
    elif tab == 'tab-3':
        return renderTest()


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
        