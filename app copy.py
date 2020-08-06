# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
#import dash_flexbox_grid as dfx
from dash.dependencies import Input, Output
import dash_daq as daq
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
#import plotly.io as pio
import pandas as pd
from math import ceil, log10
from itertools import cycle

#pio.kaleido.scope.default_format = "svg"
#external_stylesheets = ['./css/stylesheet-oil-and-gas.css']

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
#app = dash.Dash(__name__)#, external_stylesheets=external_stylesheets)
app.title = 'IRMA SPY'

def loadData(csvpath):
	return(pd.read_csv(csvpath))

def returnSegData():
	segments = df['Reference_Name'].unique()
	segset = [i.split('_')[1] for i in segments]
	segset = list(set(segset))
	segcolor = {}
	for i in range(0, len(segset)):
				segcolor[segset[i]] = px.colors.qualitative.G10[i] 
	return(segments, segset, segcolor)

def pivot4heatmap():
	df2 = df[['Sample', 'Reference_Name', 'Coverage_Depth']]
	df3 = df2.groupby(['Sample', 'Reference_Name']).mean().reset_index()
	df3[['Subtype', 'Segment', 'Group']] = df3['Reference_Name'].str.split('_', expand=True)
	df4 = df3[['Sample', 'Segment', 'Coverage_Depth']]
	#df5 = df4.pivot(columns='Sample', index='Segment', values='Coverage_Depth') # Correct format to use with px.imshow()
	return(df4)

def createheatmap(sliderMax=None):
	#df4 = pivot4heatmap()
	if sliderMax is None:
		sliderMax = df4['Coverage_Depth'].max()
	#else:
	#	sliderMax = slider_marks_r[sliderMax]
	fig = go.Figure(data=go.Heatmap( #px.imshow(df5
			x=list(df4['Sample']),
			y=list(df4['Segment']),
			z=list(df4['Coverage_Depth']), 
			zmin=0,
			zmax=sliderMax,
			colorscale='Cividis_r'))
	fig.update_layout(
		legend=dict(x=0.4, y=1.2, orientation='h')
		)
	fig.update_xaxes(side='top')
	return(fig)

def createAllCoverageFig():
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
			g_base = g.split('_')[1]
			df2 = df_thin[(df_thin['Sample'] == s) & (df_thin['Reference_Name'] == g)]
			fig.add_trace(
				go.Scatter(
					x = df2['Position'],
					y = df2['Coverage_Depth'],
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
	df2 = df[df['Sample'] == sample]
	fig = go.Figure()
	for g in segments:
		g_base = g.split('_')[1]
		df3 = df2[df2['Reference_Name'] == g]
		fig.add_trace(
			go.Scatter(
				x = df3['Position'],
				y = df3['Coverage_Depth'],
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

df = loadData('./test.csv')
segments, segset, segcolor = returnSegData()
df4 = pivot4heatmap()
sliderMax = df4['Coverage_Depth'].max()
allFig = createAllCoverageFig()


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
	[
		dcc.Store(id='store'),
		html.Img(
			src=app.get_asset_url('irma-spy.jpg'),
			height=80,
			width=80,
		),
		html.Hr(),
		dbc.Tabs(
			[
				dbc.Tab(label='Summary', tab_id='summary'),
				dbc.Tab(label='Coverage', tab_id='coverage')
			],
			id='tabs',
			active_tab='summary'
		),
		html.Div(id='tab-content')
	]
)

@app.callback(
	Output('tab-content', 'children'),
	Input('tabs', 'active_tab'), 
	Input('store', 'data')
)
def render_tab_content(active_tab, data):
	if active_tab and data is not None:
		if active_tab == 'summary':
			content = dcc.Loading(
				id='summary-loading',
				type='cube',
				children=[
					dcc.Graph(data=[[0,1,2],[0,1,2]],
						id='summary-fig'
					)
				]
			)
			return content
		elif active_tab == 'coverage':
			content = html.Div(
				dbc.Row(
					dbc.Col(
						dcc.Loading(
							id='coverageheat-loading',
							type='cube',
							children=[
								dcc.Graph(	
									id='coverage-heat'
								)
							]
						)
					)
				)
			)
			return content


'''
app.layout = html.Div(children=[
	html.Div(children=[
		html.Img(
			src=app.get_asset_url('irma-spy.jpg'),
			height=80,
			width=80,
			className='ten.columns'
		)],
		style={
			'border-style':'none none solid none',
			'border-color':'gray',
			'position':'sticky'
		},

	),
	html.Div(children=[
		dcc.Loading(
			id='coverageheat-loading',
			type='cube',
			children=[
				dcc.Graph(	
				id='coverage-heat',
				className='eleven.columns'
				)]
		)],
	className='eleven.columns'
	),
	#daq.Slider(
	#	id='heatmap-slider',
	#	max=log10(sliderMax),
	#	min=0,
	#	value=log10(1000),
	#	#handleLabel={"showCurrentValue": True,"label": "MAX"},
	#	step=1,
	#	marks=slider_marks
	#),
	html.Div(children=
		daq.Slider(
			id='heatmap-slider',
			max=1000,
			min=100,
			value=100,
			handleLabel={"showCurrentValue": True,"label": "MAX"},
			step=10
		),
		className='offset-by-eleven.columns'
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
])
'''
if __name__ == '__main__':
	app.run_server(debug=True)
