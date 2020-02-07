from webapp.jgietzen.Data import Data
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px
import plotly.graph_objects as go


from webapp.helper import log

from webapp.config import percistency, plotlyConf,  colormap

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
#                 style= plotlyConf['styles']['fullsize'],
#             )
#             ]


def renderTest():
    import dash_table
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        data.fitSurrogates()
        data.fitExplainers()
        exp = data.explainAll(0)
        slid = data.extract_features(windowsize=7, roll=False)
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

# def renderTest():
#     import dash_table
#     exists, data = Data.existsData()
#     if not exists:
#         return []
#     else:
#         slid = data.extract_features(windowsize=5, roll=True)
#         # slid = data.slide(windowsize=5)
#         return [
#             html.Div([
#             html.H5(data.originalfilename),
#             dash_table.DataTable(
#                 data=slid.head(20).to_dict('records'),
#                 columns=[{'name': i, 'id': i} for i in slid.columns]
#             ),
#             html.Hr(),  # horizontal line
#             ])
#         ]

def renderTimeseries():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            data.plotdataTimeseriesGraph()
        ]

def renderOutlierExplanation():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        # dat, layout = data.plotdataTimeseries()
        return [
            data.plotoutlierExplanationPieChartsGraph(),
            data.plotOutlierDistributionGraph(),
            data.matrixProfileGraph('outliersKnown')
        ]