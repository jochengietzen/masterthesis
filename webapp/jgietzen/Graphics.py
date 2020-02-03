from webapp.jgietzen.Data import Data
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go


from webapp.helper import percistency, plotlyConf, log, colormap

# def renderTimeseries2():
#     exists, data = Data.existsData()
#     if not exists:
#         return []
#     else:
#         dat, layout = data.plotdataTimeseries()
#         return [
#             # html.H1('Timeseries'),
#             dcc.Graph(
#                 figure = {**{'data': dat},
#                 **{'layout': dict(
#                     title='Timeseries',
#                     showlegend=True,
#                     legend=dict(
#                         x=0,
#                         y=1.2
#                     ),
#                     **plotlyConf['layout'],
#                     **layout,
#                     margin=dict(l=40, r=0, t=40, b=30)
#                 )}},
#                 id = 'timeseries-graph',
#                 config = plotlyConf['config'],
#                 style= plotlyConf['style'],
#             )
#             ]

def renderTest():
    import dash_table
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        log('lets extract')
        slid = data.extract_features(windowsize=5, roll=True)
        log('extracted')
        # slid = data.slide(windowsize=5)
        return [
            html.Div([
            html.H5(data.originalfilename),
            dash_table.DataTable(
                data=slid.head(20).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in slid.columns]
            ),
            html.Hr(),  # horizontal line
            ])
        ]

def renderTimeseries():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            data.plotdataTimeseriesGraph()
        ]