import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from flaskFiles.app import app
from flaskFiles.layouts import tabs, colors
import flaskFiles.callbacks

# from helper import *

app.layout = html.Div([
    tabs
])
# ], style = keyValuesFilter(colors, ['backgroundColor', 'color']))


if __name__ == '__main__':
    app.run_server(debug=True)