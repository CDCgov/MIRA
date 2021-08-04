import base64
import datetime
import io
import os
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import re
import pandas as pd


app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

pathway = '/scicomp/groups/OID/NCIRD/ID-OD/ISA/by-instrument'
'''
def filesInFolderTree(startPath):
	dirPath = os.path.realpath(startPath)
	listOfFileNames = [ os.path.join(root, name) \
						for root, dirs, files in os.walk(dirPath) \
						for name in sorted(dirs) \
						if re.search(r'[0-9]{6}_.+?_[0-9]{5}_.+?$', name)]
	return listOfFileNames
@app.callback(
    dash.dependencies.Output("select_machine", "options"),
    [dash.dependencies.Input("select_machine", "search_value")],
)
def update_options(search_value):
    if not search_value:
        raise dash.exceptions.PreventUpdate
    return [o for o in search_value if search_value in o["label"]]
'''
@app.callback(
	Output('select_run', 'options'),
	Input('select_machine', 'value'))
def select_run(machine):
	print(os.path.join(pathway, machine))
	if not machine:
		raise dash.exceptions.PreventUpdate
	options = [{'label':i, 'value':i} for i in sorted(os.listdir(os.path.join(pathway ,machine)))] #filesInFolderTree(os.path.join(pathway, machine))]
	return options

@app.callback(
	Output('select_run', 'value'),
	Input('select_run', 'options'))
def set_run_options(run_options):
	print(run_options)
	if not run_options:
		raise dash.exceptions.PreventUpdate
	return run_options[0]['value']

@app.callback(
	Output('display-selected-values', 'children'),
	Input('select_machine', 'value'),
	Input('select_run', 'value'),
	prevent_initial_call=True)
def set_display_children(machine, run):
	return 'machine = {}\trun = {}\npathway = {}'.format(machine, run, os.path.join(pathway, machine, run)) 

app.layout = html.Div([
	dcc.Dropdown(id='select_machine',
				options=[{'label':i, 'value':i} for i in sorted(os.listdir(pathway))],
				placeholder='Select sequencing instrument: ',
	),
	html.Hr(),
	dcc.Dropdown(id='select_run',
				placeholder='Select IRMA output directory: ',
	),
	html.Hr(),
	html.Div(id='display-selected-values')
])

if __name__ == '__main__':
	app.run_server(host= '0.0.0.0', debug=True)

