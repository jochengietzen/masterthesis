from jgietzen.Data import Data
import dash_core_components as dcc
import dash_html_components as html
import plotly_express as px


from helper import percistency, plotlyConf, log

def renderTimeseries():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        dat, layout = data.plotdataTimeseries()
        return [
            # html.H1('Timeseries'),
            dcc.Graph(
                figure = {**{'data': dat},
                **{'layout': dict(
                    title='Timeseries',
                    showlegend=True,
                    legend=dict(
                        x=0,
                        y=1.2
                    ),
                    **plotlyConf['layout'],
                    **layout,
                    margin=dict(l=40, r=0, t=40, b=30)
                )}},
                id = 'timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['style'],
            )
            ]

def renderTimeseries2():
    exists, data = Data.existsData()
    if not exists:
        return []
    else:
        dat, layout = data.plotdataTimeseries()
        log(data.df)
        fig = px.area(data.df, x=data.column_sort, y="y", color=data.column_outlier)
        return [
            dcc.Graph(id='timeseries-graph',
                config = plotlyConf['config'],
                style= plotlyConf['style'],
                figure = fig
            )
        ]