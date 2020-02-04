import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from webapp.config import createdirs
from webapp.flaskFiles.applicationProvider import app, server
from webapp.flaskFiles.layouts import tabs, colors
import webapp.flaskFiles.callbacks

app.layout = html.Div([
    tabs
])


if __name__ == '__main__':
    createdirs()
    app.run_server(debug=True)