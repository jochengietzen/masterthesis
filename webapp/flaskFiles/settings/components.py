import dash_core_components as dcc
import dash_html_components as html
from .styles import\
    deleteButtonDivStyle, uploadStyle, dropDownStyle, maxwidth200

ids = dict(deleteButton = 'delete-data')

deleteButton = html.Button('Delete data', id=ids['deleteButton'])

deleteButtonDiv = html.Div(deleteButton, id='delete-data-div', style=deleteButtonDivStyle)

uploadComponent = dcc.Upload(id='upload-data',children=html.Div(['Drag and Drop or ',html.A('Select Files')]),style=uploadStyle)

colIdLabel = html.Label('Timeseries Id column')
colIdDiv = html.Div([colIdLabel])
colSortLabel = html.Label('Timestamp column')
colSortDiv = html.Div([colSortLabel])
colFrequencyLabel = html.Label('Frequency of data')
colFrequencyDiv = html.Div([colFrequencyLabel], id = 'input-frequency-div', style = maxwidth200)
colOutlierLabel = html.Label('Outlier column')
colOutlierDiv = html.Div([colOutlierLabel])
colRelevantLabel = html.Label('Relevant columns to take a look at')
colRelevantDiv = html.Div([colRelevantLabel])
saveResultsLabel = html.Label('Show updates')
saveResultsDiv = html.Div([saveResultsLabel], id='refresh-button')

colId = dcc.Dropdown(id='dd-column-id', style = dropDownStyle)
colSort = dcc.Dropdown(id='dd-column-sort', style = dropDownStyle)
colIsTimestamp = dcc.RadioItems(id='ri-is-timestamp',options=[dict(label='Is Timestamp in [s]', value='True'), dict(label='Not a Timestamp', value='False')])
colFrequency = dcc.Input(id='input-frequency', type='number', placeholder=1000)
buttonClearFrequency = html.Button('Clear Frequency', id='clear-frequency')
colFrequencyDiv.children = colFrequencyDiv.children + [colFrequency, buttonClearFrequency]
colOutlier = dcc.Dropdown(id='dd-column-outlier', multi=True, style = dropDownStyle)
colRelevant = dcc.Dropdown(id = 'dd-columns-relevant', style = dropDownStyle, multi=True)