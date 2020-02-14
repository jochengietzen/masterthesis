import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from .styles import\
    buttonDivStyle, uploadStyle, dropDownStyle, maxwidth200, displaynone

ids = dict(deleteButton = 'delete-data', saveButton = 'save-button',
deleteButtonDiv = 'delete-data-div',
saveButtonDiv = 'save-data-div',
uploadComponent = 'upload-data',
saveResultsDiv = 'refresh-button',
colId = 'dd-column-id',
colSort = 'dd-column-sort',
colIsTimestamp = 'ri-is-timestamp',
colFrequency = 'input-frequency',
buttonClearFrequency = 'clear-frequency',
colOutlier = 'dd-column-outlier'
)

deleteButton = html.Button('Delete data', id=ids['deleteButton'])
deleteButtonDiv = html.Div(deleteButton, id=ids['deleteButtonDiv'], style=buttonDivStyle)

saveButton = html.Button('Save data', id=ids['saveButton'])
saveButtonDiv = html.Div(saveButton, id=ids['saveButtonDiv'], style={**buttonDivStyle, **displaynone})
saveButtonInputClick = Input(ids['saveButton'], 'n_clicks')

uploadComponent = dcc.Upload(id=ids['uploadComponent'],children=html.Div(['Drag and Drop or ',html.A('Select Files')]),style=uploadStyle)

dataUploadOutput = Output('output-data-upload', 'children')
dataUploadContentsInput = Input('upload-data', 'contents')
uploadStates = [State('upload-data', 'filename'), State('upload-data', 'last_modified')]

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
saveResultsDiv = html.Div([saveResultsLabel], id=ids['saveResultsDiv'])

colId = dcc.Dropdown(id=ids['colId'], style = dropDownStyle)
colSort = dcc.Dropdown(id=ids['colSort'], style = dropDownStyle)
colIsTimestamp = dcc.RadioItems(id=ids['colIsTimestamp'],options=[dict(label='Is Timestamp in [s]', value='True'), dict(label='Not a Timestamp', value='False')])
colFrequency = dcc.Input(id=ids['colFrequency'], type='number', placeholder=1000)
buttonClearFrequency = html.Button('Clear Frequency', id=ids['buttonClearFrequency'])
colFrequencyDiv.children = colFrequencyDiv.children + [colFrequency, buttonClearFrequency]
colOutlier = dcc.Dropdown(id=ids['colOutlier'], multi=True, style = dropDownStyle)
colRelevant = dcc.Dropdown(id = 'dd-columns-relevant', style = dropDownStyle, multi=True)