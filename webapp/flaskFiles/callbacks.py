from dash.dependencies import Input, Output

from webapp.flaskFiles.applicationProvider import app, server, session
from webapp.flaskFiles.dash_upload import getUploadHTML
from webapp.flaskFiles.settings import getSettingsHTML
from webapp.flaskFiles.explanation import getExplanationHTML

tabRouting = {
    'tab-upload': getUploadHTML,
    'tab-settings': getSettingsHTML,
    'tab-explanation': getExplanationHTML,
}

import sys
from webapp.helper import log
from webapp.config import dir_sessions
import json

from webapp.flaskFiles.DataHandler import existsData


import webapp.flaskFiles.sessionHandling

@app.callback(Output('tabs-content', 'children'),
    [Input('tabs', 'value')]
)
def render_tab(tab):
    if tab in tabRouting:
        return tabRouting[tab]() if callable(tabRouting[tab]) else tabRouting[tab]
    else:
        return []

