import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, session
from flask_session import Session
from datetime import timedelta
from webapp.config import dir_sessions

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

server.config['SESSION_PERMANENT'] = True
server.config['SESSION_TYPE'] = 'filesystem'
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

# The maximum number of items the session stores 
# before it starts deleting some, default 500
server.config['SESSION_FILE_THRESHOLD'] = 3  
# server.config['SECRET_KEY'] = 'MAKE THIS SECRET'
server.config['SESSION_FILE_DIR'] = dir_sessions

sess = Session(server)
session = session
app.config.suppress_callback_exceptions = True
