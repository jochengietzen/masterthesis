import dash_core_components as dcc
import dash_html_components as html

from webapp.flaskFiles.applicationProvider import app as app

th = 25
tab_styles = {
    "fontSize": "12pt",
    "height": "{}px".format(th),
    "width": "100vw"
}

tab_style = {
    'paddingTop': '0px',
    'backgroundColor': 'rgba(0,0,0,.15)'
}

tab_selected = { **tab_style,
    'backgroundColor': 'white'
    # 'width': 'calc(100% / 5)'
}

colors = {
    'backgroundColor': '#111111',
    'text': '#7FDBFF'
}

tabs =  html.Div([
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Upload', value='tab-upload', style=tab_style, selected_style=tab_selected),
        dcc.Tab(label='Settings', value='tab-settings', style=tab_style, selected_style=tab_selected),
        dcc.Tab(label='Outlier explanation', value='tab-explanation', style=tab_style, selected_style=tab_selected),
    ], style=tab_styles, persistence=True, persistence_type='session'),
    html.Div(id='tabs-content')
])



