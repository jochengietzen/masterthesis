from jgietzen.Data import Data
import dash_core_components as dcc
import dash_html_components as html

from helper import percistency, plotlyConfig

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
                    **layout,
                    margin=dict(l=40, r=0, t=40, b=30)
                )}},
                id = 'timeseries-graph',
                config = plotlyConfig
            )
            ]
