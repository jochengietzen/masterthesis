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
    'paddingTop': '0px'
}

tab_selected = { **tab_style,
    # 'backgroundColor': 'yellow'
    'width': '40%'
}

colors = {
    'backgroundColor': '#111111',
    'text': '#7FDBFF'
}

tabs =  html.Div([
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Data configuration', value='tab-1', style=tab_style, selected_style=tab_selected),
        dcc.Tab(label='Data preview', value='tab-2', style=tab_style, selected_style=tab_selected),
    ], style=tab_styles, persistence=True, persistence_type='session'),
    html.Div(id='tabs-content')
])



