import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from webapp.helper import castlist
from .styles import\
    *
    # buttonDivStyle, uploadStyle, dropDownStyle, maxwidth200

ids = dict(
    deleteButton = 'delete-data',
    saveButton = 'save-data',
    deleteButtonDiv = 'delete-data-div',
    saveButtonDiv = 'delete-data-div',
    dataChoiceDiv = 'data-choice-div',
    dataChoice = 'data-choice',
    dataChoiceHidden = 'data-choice-hidden',
    clearFrequency = 'clear-frequency'
    )

deleteButton = html.Button('Delete data', id=ids['deleteButton'])
saveButton = html.Button('Save data', id=ids['saveButton'])

deleteButtonDiv = html.Div(deleteButton, id=ids['deleteButtonDiv'], style=buttonDivStyle)
saveButtonDiv = html.Div(saveButton, id=ids['saveButtonDiv'], style=buttonDivStyle)

dataChoice = dcc.Dropdown(value = None, id=ids['dataChoice'], style = {**dropDownStyle, **minwidth200})
dataChoiceHidden = html.Div(id=ids['dataChoiceHidden'], style = displaynone)
dataChoiceDiv = html.Div([dataChoiceHidden, dataChoice], id=ids['dataChoiceDiv'], style={**fullparentwidth, **flexcenter})

updateTriggerDivs = lambda x: [html.Div(id=f'update-trigger-{i + 1}', style=displaynone) for i in range(x)]
updateTriggerOutput = lambda index: Output(f'update-trigger-{index}', 'children')
updateTriggerInput = lambda indexes: [Input(f'update-trigger-{i}', 'children') for i in castlist(indexes)]

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

colId = dcc.Dropdown(id='dd-column-id', style = dropDownStyle)
colSort = dcc.Dropdown(id='dd-column-sort', style = dropDownStyle)
colIsTimestamp = dcc.RadioItems(id='ri-is-timestamp',options=[dict(label='Is Timestamp in [s]', value='True'), dict(label='Not a Timestamp', value='False')])
colFrequency = dcc.Input(id='input-frequency', type='number', placeholder=1000)
buttonClearFrequency = html.Button('Clear Frequency', id=ids['clearFrequency'])
colFrequencyDiv.children = colFrequencyDiv.children + [colFrequency, buttonClearFrequency]
colOutlier = dcc.Dropdown(id='dd-column-outlier', multi=True, style = dropDownStyle)
colRelevant = dcc.Dropdown(id = 'dd-columns-relevant', style = dropDownStyle, multi=True)

