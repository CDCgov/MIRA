# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
#import dash_flexbox_grid as dfx
from dash.dependencies import Input, Output, State
import dash_daq as daq
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
#import plotly.io as pio
import pandas as pd
from math import ceil, log10
from itertools import cycle
import pickle
from sys import path, argv
from os.path import dirname, realpath
import os
import yaml
path.append(dirname(realpath(__file__))+'/scripts/')
import irma2dash


#pio.kaleido.scope.default_format = "svg"
#external_stylesheets = ['./css/stylesheet-oil-and-gas.css']

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
#app = dash.Dash(__name__)#, external_stylesheets=external_stylesheets)
app.title = 'IRMA SPY'
app.config['suppress_callback_exceptions'] = True

with open(argv[1], 'r') as y:
	CONFIG = yaml.safe_load(y)
pathway = CONFIG['PATHWAY']

@app.callback(
    Output('select_run', 'options'),
    Input('select_machine', 'value'))
def select_run(machine):
    print(os.path.join(pathway, machine))
    if not machine or machine == 'Select sequencing instrument: ':
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

def returnSegData():
	segments = df['Reference_Name'].unique()
	try:
		segset = [i.split('_')[1] for i in segments]
	except IndexError:
		segset = segments
	segset = list(set(segset))
	segcolor = {}
	for i in range(0, len(segset)):
				segcolor[segset[i]] = px.colors.qualitative.G10[i] 
	return(segments, segset, segcolor)

def pivot4heatmap():
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	df2 = df[['Sample', 'Reference_Name', cov_header]]
	df3 = df2.groupby(['Sample', 'Reference_Name']).mean().reset_index()
	try:
		df3[['Subtype', 'Segment', 'Group']] = df3['Reference_Name'].str.split('_', expand=True)
	except ValueError:
		df3[['Segment']] = df3['Reference_Name']
	df4 = df3[['Sample', 'Segment', cov_header]]
	#df5 = df4.pivot(columns='Sample', index='Segment', values='Coverage_Depth') # Correct format to use with px.imshow()
	return(df4)

def createheatmap(sliderMax=None):
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	#df4 = pivot4heatmap()
	if sliderMax is None:
		sliderMax = df4[cov_header].max()
	#else:
	#	sliderMax = slider_marks_r[sliderMax]
	fig = go.Figure(
			data=go.Heatmap( #px.imshow(df5
				x=list(df4['Sample']),
				y=list(df4['Segment']),
				z=list(df4[cov_header]), 
				zmin=0,
				zmax=sliderMax,
				colorscale='Cividis_r',
				hovertemplate='%{y} = %{z:,.0f}x<extra>%{x}<br></extra>'
				)
			)
	fig.update_layout(
		legend=dict(x=0.4, y=1.2, orientation='h')
		)
	fig.update_xaxes(side='top')
	return(fig)

def createAllCoverageFig():
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	samples = df['Sample'].unique()

	fig_numCols = 4
	fig_numRows = ceil(len(samples) / fig_numCols)

	pickCol = cycle(list(range(1,fig_numCols+1))) # next(pickCol)
	pickRow = cycle(list(range(1, fig_numRows+1))) # next(pickRow)
	
	# Take every 10th row of data
	df_thin = df.iloc[::10, :]

	fig = make_subplots(
			rows=fig_numRows,
			cols=fig_numCols,
			shared_xaxes='all',
			subplot_titles = (samples),
			vertical_spacing = 0.02,
			horizontal_spacing = 0.02
			)

	for s in samples:
		r,c = next(pickRow), next(pickCol)
		for g in segments:
			try:
				g_base = g.split('_')[1]
			except IndexError:
				g_base = g
			df2 = df_thin[(df_thin['Sample'] == s) & (df_thin['Reference_Name'] == g)]
			fig.add_trace(
				go.Scatter(
					x = df2['Position'],
					y = df2[cov_header],
					mode = 'lines',
					line = go.scatter.Line(color=segcolor[g_base]),
					name = g,
					customdata = df2['Sample']
				),
				row = r,
				col = c
			)
	fig.update_layout(
		margin=dict(l=0, r=0, t=40, b=0),
		height=1200,
		showlegend=False)
	return(fig)

def createSampleCoverageFig(sample):
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	df2 = df[df['Sample'] == sample]
	fig = go.Figure()
	for g in segments:
		try:
			g_base = g.split('_')[1]
		except IndexError:
			g_base = g
		df3 = df2[df2['Reference_Name'] == g]
		fig.add_trace(
			go.Scatter(
				x = df3['Position'],
				y = df3[cov_header],
				mode = 'lines',
				line = go.scatter.Line(color=segcolor[g_base]),
				name = g,
				customdata = tuple(['all']*len(df3['Sample']))
			))
	fig.update_layout(
		height=600,
		title=sample,
		yaxis_title='Coverage',
		xaxis_title='Position')
	return(fig)


df = irma2dash.dash_irma_coverage_df(argv[2]) #loadData('./test.csv')
df.to_parquet(argv[2]+'/coverage.parquet')
#df.to_pickle(argv[2]+'/coverage.pkl')

segments, segset, segcolor = returnSegData()
df4 = pivot4heatmap()
df4.to_csv(argv[2]+'/mean_coverages.tsv', sep='\t', index=False)
if 'Coverage_Depth' in df4.columns:
	cov_header = 'Coverage_Depth'
else:
	cov_header = 'Coverage Depth'
sliderMax = df4[cov_header].max()
allFig = createAllCoverageFig()

@app.callback(Output('output-data-upload', 'children'),
	Input('upload-data', 'contents'),
	State('upload-data', 'filename'),
	State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
	if list_of_contents is not None:
		children = [
			parse_contents(c, n, d) for c, n, d in
			zip(list_of_contents, list_of_names, list_of_dates)]
		return children

@app.callback(
	dash.dependencies.Output('coverage-heat', 'figure'),
	[dash.dependencies.Input('heatmap-slider', 'value')])
def callback_heatmap(maximumValue):
	#return(createheatmap(int(slider_marks[str(maximumValue)])))
	return(createheatmap(maximumValue))

previousClick, returnClick = 0,0
@app.callback(
	dash.dependencies.Output('coverage', 'figure'),
	[dash.dependencies.Input('coverage-heat', 'clickData'),
	dash.dependencies.Input('backButton', 'n_clicks')])
def callback_coverage(plotClick, buttonClick):
	global segcolor, previousClick, returnClick
	returnClick = buttonClick
	print(plotClick)
	if returnClick is None:
		returnClick = 0
	print("return={}\tprevious={}".format(returnClick, previousClick))
	if plotClick is None or returnClick > previousClick:
		previousClick = returnClick
		return(allFig)
	elif plotClick['points'][0]['x'] != 'all':
		s = plotClick['points'][0]['x']
		return(createSampleCoverageFig(s))	
	return(fig)

########################################################
#################### LAYOUT TABS #######################
########################################################
@app.callback(
	Output('tab-content', 'children'),
	[Input('tabs', 'active_tab'), 
	Input('store', 'data')]
)
def render_tab_content(active_tab, data):
	print(data)
	if active_tab:# and data is not None:
		if active_tab == 'summary':
			content = dcc.Loading(
				id='summary-loading',
				type='cube',
				children=[
					dcc.Graph(
						id='summary-fig'
					)
				]
			)
			return content
		elif active_tab == 'coverage':
			content = html.Div(
				[dbc.Row(
					[dbc.Col(
						dcc.Loading(
							id='coverageheat-loading',
							type='cube',
							children=[
								dcc.Graph(	
									id='coverage-heat'
								)
							]
						),
						width=11,
						align='end'
					),
					dbc.Col(
						daq.Slider(
							id='heatmap-slider',
							marks={'100':'100','300':'300','500':'500','700':'700','900':'900'},
							max=1000,
							min=100,
							value=100,
							#handleLabel={"showCurrentValue": True,"label": "MAX", 'style':{}},
							step=50,
							vertical=True,
							persistence=True,
							dots=True
						),
						align='center'
					)],
					no_gutters=True
				),
				dcc.Loading(
					id='coverage-loading',
					type='cube',
					children=dcc.Graph(
						id='coverage',
						className='twelve columns'
					)
				),
				html.Div(children=[
					html.Button('All figures',
					id='backButton',
					className='button'
					)]
				)
				]
			)
			return content



########################################################
###################### LAYOUT ##########################
########################################################

# Layout Functions
def slider_marks(maxvalue):
	linearStep = 1
	i = 1
	marks = {str(linearStep):str(i)}
	while i <= maxvalue:
		linearStep += 1
		i = i*10
		marks[str(linearStep)] = str(i)
	return(marks)

slider_marks = slider_marks(sliderMax)
slider_marks_r = {}
for k,v in slider_marks.items():
	slider_marks_r[v] = k
#print(slider_marks)
#print(slider_marks_r)

app.layout = dbc.Container(
	fluid=True,
	children=
	[
		dcc.Store(id='store'),
		html.Div([
			html.Img(
				src=app.get_asset_url('irma-spy.jpg'),
				height=80,
				width=80,
			),
			dcc.Dropdown(id='select_machine',
				options=[{'label':i, 'value':i} for i in sorted(os.listdir(pathway))],
				placeholder='Select sequencing instrument: ',
			),
			dcc.Dropdown(id='select_run',
				placeholder='Select IRMA output directory: ',
			),
		]),
		dbc.Tabs(
			[
				dbc.Tab(label='Summary', tab_id='summary'),
				dbc.Tab(label='Coverage', tab_id='coverage')
			],
			id='tabs',
			active_tab='coverage'
		),
		html.Div(id='tab-content')
	]
)

####################################################
####################### MAIN #######################
####################################################
if __name__ == '__main__':
	app.run_server(host= '0.0.0.0', debug=True)
