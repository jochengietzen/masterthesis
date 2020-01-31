from dash.dependencies import Input, Output

from flaskFiles.app import app, session
from flaskFiles.dash_upload import getUploadHTML
import uuid

import sys
log = lambda content: print(content, file = sys.stdout)

from jgietzen.Graphics import renderTimeseries

@app.server.before_request
def uid():
    if 'uid' not in session:
        log(session)
        session['uid'] = uuid.uuid4().__str__()

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_tab(tab):
    log(session)
    if tab == 'tab-1':
        return getUploadHTML()
    elif tab == 'tab-2':
        return renderTimeseries()


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
        