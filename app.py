# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_bio as dbio
#import dash_flexbox_grid as dfx
from dash.dependencies import Input, Output, State
import dash_daq as daq
import dash_table
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pandas as pd
from math import ceil, log10
from itertools import cycle
import pickle
from sys import path, argv
from os.path import dirname, realpath, isdir
import os
import yaml
import json
from glob import glob
from numpy import arange
from flask_caching import Cache
path.append(dirname(realpath(__file__))+'/scripts/')
import irma2dash
import conditional_color_range_perCol

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
app.title = 'IRMA SPY'
app.config['suppress_callback_exceptions'] = True

cache_timeout = 60*60*24
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
cache.clear()

with open(argv[1], 'r') as y:
	CONFIG = yaml.safe_load(y)
pathway = CONFIG['PATHWAY']

@app.callback(
	Output('select_run', 'options'),
	Input('select_machine', 'value'))
def select_run(machine):
	if not machine or machine == 'Select sequencing instrument: ':
		raise dash.exceptions.PreventUpdate
	options = [{'label':i, 'value':i} for i in sorted(os.listdir(os.path.join(pathway ,machine))) if i[0] != '.'] #filesInFolderTree(os.path.join(pathway, machine))]
	return options

@app.callback(
	[Output('select_run', 'value')],
	Input('select_run', 'options'))
def set_run_options(run_options):
	if not run_options:
		raise dash.exceptions.PreventUpdate
	return run_options[0]['value']

@app.callback(
	Output('select_irma', 'options'),
	[Input('select_machine', 'value'),
	Input('select_run', 'value')])
def select_irma(machine, run):
	if not machine or not run:
		raise dash.exceptions.PreventUpdate
	options = [{'label':i, 'value':i} for i in sorted(os.listdir(os.path.join(pathway, machine, run)))] #filesInFolderTree(os.path.join(pathway, machine))]
	return options

@app.callback(
	Output('select_irma', 'value'),
	Input('select_irma', 'options'))
def set_irma_options(irma_options):
	if not irma_options:
		raise dash.exceptions.PreventUpdate
	return irma_options[0]['value']

previousClick = 0
@app.callback(
	[Output('select_sample', 'options'),
	Output('select_sample', 'value')],
	[Input('coverage-heat', 'clickData'),
	Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value')])
@cache.memoize(timeout=cache_timeout)
def select_sample(plotClick, machine, run, irma):
	#df = pd.read_json(json.loads(data)['df4'], orient='split')
	df = pd.read_json(json.loads(generate_df(machine, run, irma))['df4'], orient='split')
	samples = df['Sample'].unique()
	samples.sort()
	options = [{'label':i, 'value':i} for i in samples]
	global previousClick
	if not plotClick:
		value = samples[0]
	elif plotClick == previousClick:
		sample = sample
	elif plotClick['points'][0]['x'] != 'all':
		previousClick = plotClick
		value = plotClick['points'][0]['x']
	return options, value

#@app.callback(
#	Output('select_sample', 'value'),
#	Input('select_sample', 'options'))
#def set_irma_options(sample_options):
#	if not sample_options:
#		raise dash.exceptions.PreventUpdate
#	return sample_options[0]['value']

@app.callback(
	Output('single_sample_figs', 'children'),
	[Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value'),
	Input('select_sample', 'value')])
@cache.memoize(timeout=cache_timeout)
def single_sample_fig(machine, run, irma, sample):
	#print('single_sample_callback triggered mahine={}, run={}, irma={}, sample={}'.format(machine,run,irma,sample))
	if not machine or not run or not irma or not sample:
		print('exception raised')
		raise dash.exceptions.PreventUpdate
	#print('reading read_df')
	df = pd.read_json(json.loads(generate_df(machine, run, irma))['read_df'], orient='split')
	#print('done')
	df = df[df['Sample'] == sample]
	#print(df)
	sankeyfig = irma2dash.dash_reads_to_sankey(df)
	#print(sankeyfig)
	df = pd.read_json(json.loads(generate_df(machine, run, irma))['df'], orient='split')
	#print(df)
	#df = pd.read_json(json.loads(data)['df'], orient='split')
	segments = json.loads(generate_df(machine, run, irma))['segments']
	segcolor = json.loads(generate_df(machine, run, irma))['segcolor']
	#segments, segcolor = json.loads(data)['segments'], json.loads(data)['segcolor']
	coveragefig = createSampleCoverageFig(sample, df, segments, segcolor)
	#content = html.Div(
	content = dbc.Row(
                    [dbc.Col(dcc.Graph(figure=sankeyfig),
                        	width=4,
                        	align='start'),
					dbc.Col(dcc.Graph(figure=coveragefig),
						width=8,
						align='center')
					],
					no_gutters=True
				 )
			#  )
	#print(content)
	return content

#@app.callback(
#	Output('df_cache', 'data'),
#	[Input('select_machine', 'value'),
#	Input('select_run', 'value'),
#	Input('select_irma', 'value')])
@cache.memoize(timeout=cache_timeout)
def generate_df(machine, run, irma):
	if not machine or not run or not irma:
		raise dash.exceptions.PreventUpdate
	irma_path = os.path.join(pathway, machine, run, irma)
	df = irma2dash.dash_irma_coverage_df(irma_path) #argv[2]) #loadData('./test.csv')
	read_df = irma2dash.dash_irma_reads_df(irma_path)
	segments, segset, segcolor = returnSegData(df)
	df4 = pivot4heatmap(df)
	df4.to_csv(irma_path+'/mean_coverages.tsv', sep='\t', index=False)
	if 'Coverage_Depth' in df4.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	sliderMax = df4[cov_header].max()
	allFig = createAllCoverageFig(df, ','.join(segments), segcolor)
	print('creating irma_read_fig')
	irma_read_fig = create_irma_read_fig(read_df)
	return json.dumps({'df':df.to_json(orient='split'), 
						'df4':df4.to_json(orient='split'), 
						'read_df':read_df.to_json(orient='split'), 
						'cov_header':cov_header, 
						'sliderMax':sliderMax,
						'segments':','.join(segments),
						'segset':','.join(segset),
						'segcolor':segcolor,
						'allFig':allFig.to_json(),
						'irma_reads_fig':irma_read_fig.to_json()})

@app.callback(
	[Output('illumina_demux_table', 'children'),
	Output('demux_fig', 'figure')],
	[Input('select_machine', 'value'),
	Input('select_run', 'value')])
@cache.memoize(timeout=cache_timeout)
def illumina_demux_table(machine, run):
	if not machine or not run:
		raise dash.exceptions.PreventUpdate
	glob_string = '{}/Reports/html/*/all/all/all/*{}*'.format(os.path.join(pathway, machine, run), run)
	f = glob(glob_string)
	df = pd.read_html(f[0])[2]
	fill_colors = conditional_color_range_perCol.discrete_background_color_bins(df, 10, ['PF Clusters', '% of thelane', '% Perfectbarcode', 'Yield (Mbases)', '% PFClusters', '% >= Q30bases', 'Mean QualityScore', '% One mismatchbarcode'])
	table = html.Div([
			dash_table.DataTable(
				columns = [{"name": i, "id": i} for i in df.columns],
				data = df.to_dict('records'),
				sort_action='native',
				style_data_conditional=fill_colors
			)
		])
	fig = px.pie(df, values='PF Clusters', names='Sample')
	fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
	fig.update_traces(showlegend=False, textinfo='none')
	return table, fig

def create_irma_read_fig(df):
	columns = 12
	rows = 24
	s = '{"type":"domain"} ' * columns
	specs = []
	for i in range(0,rows):
		specs.append([json.loads(a) for a in s.split()])
	fig = make_subplots(rows, columns, specs=specs)
	col_n, row_n = cycle([i for i in range(1,columns+1)]), cycle([i for i in range(1,rows+1)])
	counter = 0
	annotations = []
	for sample in set(list(df['Sample'])):
		counter += 1
		if counter % 4 == 1:
			r = next(row_n)
		stage_counter = 0
		for stage in [[2], [3], [4,5]]:
			c = next(col_n)
			stage_counter += 1
			d2 = df[(df['Stage'].isin(stage)) & (df['Sample'] == sample)]
			fig.add_trace(go.Pie(values=d2['Reads'], labels=d2['Record'], name=sample, meta=[sample],
								hovertemplate="%{meta[0]} <br> %{label} </br> <br> %{percent} </br> %{value} reads <extra></extra> "),
							row=r, col=c)
	fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), 
						height=3200, 
						hoverlabel=dict(bgcolor='white', 
										font_size=16, 
										namelength=-1
									)
					)
	fig.update_traces(showlegend=False, textinfo='none')
	return fig
		

@cache.memoize(timeout=cache_timeout)
def returnSegData(df):
	segments = df['Reference_Name'].unique()
	try:
		segset = [i.split('_')[1] for i in segments]
	except IndexError:
		segset = segments
	segset = list(set(segset))
	segcolor = {}
	for i in range(0, len(segset)):
				segcolor[segset[i]] = px.colors.qualitative.G10[i] 
	return segments, segset, segcolor

@cache.memoize(timeout=cache_timeout)
def pivot4heatmap(df):
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
	return df4

@cache.memoize(timeout=cache_timeout)
def createheatmap(df4, sliderMax=None):
	if 'Coverage_Depth' in df4.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	if sliderMax is None:
		sliderMax = df4[cov_header].max()
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

def createAllCoverageFig(df, segments, segcolor):
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	samples = df['Sample'].unique()
	fig_numCols = 4
	fig_numRows = ceil(len(samples) / fig_numCols)
	pickCol = cycle(list(range(1,fig_numCols+1))) # next(pickCol)
	pickRow = cycle(list(range(1, fig_numRows+1))) # next(pickRow)
	# Take every 20th row of data
	df_thin = df.iloc[::20, :]
	fig = make_subplots(
			rows=fig_numRows,
			cols=fig_numCols,
			shared_xaxes='all',
			shared_yaxes=False,
			subplot_titles = (samples),
			vertical_spacing = 0.02,
			horizontal_spacing = 0.02
			)
	for s in samples:
		r,c = next(pickRow), next(pickCol)
		for g in segments.split(','):
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
	def pick_total_height(num_samples):
		if num_samples <= 40:
			return 1200
		else:
			return 2400
	fig.update_layout(
		margin=dict(l=0, r=0, t=40, b=0),
		height=pick_total_height(len(samples)),
		showlegend=False)
	return(fig)

@cache.memoize(timeout=cache_timeout)
def createSampleCoverageFig(sample, df, segments, segcolor):
	if 'Coverage_Depth' in df.columns:
		cov_header = 'Coverage_Depth'
	else:
		cov_header = 'Coverage Depth'
	df2 = df[df['Sample'] == sample]
	fig = go.Figure()
	for g in segments.split(','):
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

@app.callback(
	Output('coverage-heat', 'figure'),
	[Input('heatmap-slider', 'value'),
	Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value')])
@cache.memoize(timeout=cache_timeout)
def callback_heatmap(maximumValue, machine, run, irma):
	df = pd.read_json(json.loads(generate_df(machine, run, irma))['df4'], orient='split')
	#df = pd.read_json(json.loads(data)['df4'], orient='split')
	return(createheatmap(df, maximumValue))

@app.callback(
	Output('select_gene', 'options'),
	[Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value')])
def select_run(machine, run, irma):
	if not machine or not run or not irma:
		raise dash.exceptions.PreventUpdate
	options = [{'label':i.split('.')[0], 'value':i.split('.')[0]} for i in sorted(os.listdir(os.path.join(pathway ,machine, run,irma))) if 'consensus' not in i and 'fasta' in i ] #filesInFolderTree(os.path.join(pathway, machine))]
	return options

@app.callback(
	[Output('select_gene', 'value')],
	Input('select_gene', 'options'))
def set_run_options(gene_options):
	if not gene_options:
		raise dash.exceptions.PreventUpdate
	return gene_options[0]['value']

@app.callback(
	Output('alignment_fig', 'children'),
	[Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value'),
	Input('select_gene', 'value')])
#@cache.memoize(timeout=cache_timeout)
def alignment_fig(machine, run, irma, gene):
	if not machine or not run or not irma or not gene:
		raise dash.exceptions.PreventUpdate
	with open(os.path.join(pathway, machine, run, irma, '{}.fasta'.format(gene)), 'r') as d:
		data = '\n'.join(d.readlines())
	return dbio.AlignmentChart(data=data, showgap=False, showid=False)


@app.callback(
	Output('aa_var_table', 'children'),
	[Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value')])
def aa_var_table(machine, run, irma):
	df = pd.read_csv(os.path.join(pathway, machine, run, irma, 'AAvariants.txt'), sep='\t')
	table = dash_table.DataTable(
				columns = [{"name": i, "id": i} for i in df.columns],
				data = df.to_dict('records'),
				sort_action='native',
				filter_action='native',
				page_size=20
			)
	return table

#@app.callback(
#	Output('irma-reads', 'figure'),
#	Input('df_cache', 'data'))
#def callback_irma_read_fig(data):
#	df = pd.read_json(json.loads(generate_df(machine, run, irma))['df'], orient='split')
	#fig = pio.from_json(json.loads(data)['irma_reads_fig'])
#	return fig


########################################################
#################### LAYOUT TABS #######################
########################################################
@app.callback(
	Output('tab-content', 'children'),
	[Input('tabs', 'active_tab'), 
	#Input('store', 'data')]
	Input('select_machine', 'value'),
	Input('select_run', 'value'),
	Input('select_irma', 'value')]
)
def render_tab_content(active_tab, machine, run, irma):
	if active_tab:
		if active_tab == 'demux':
			if 'MinION' in machine:
				with open(glob(os.path.join(pathway, machine, run,'*pycoQC.html'))[0], 'r') as d:
					raw_html = '\n'.join(d.readlines())
				content = dcc.Loading(
					id='demux-ont-loading',
					type='cube',
					children=[
						html.Iframe(srcDoc=raw_html, height=10000, width=1400)
					]
				)
				return content
			else:
				content = dcc.Loading(
					id='demux-loading',
					type='cube',
					children=[
						dcc.Graph(
							id='demux_fig'
						),
						html.Div(
							id='illumina_demux_table'
						)
					]
				)
				return content
		elif active_tab == 'irma':
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
									step=50,
									vertical=True,
									persistence=True,
									dots=True
								),
								align='center'
							)],
							no_gutters=True
						),
						dcc.Dropdown(id='select_sample',persistence=True),
						html.Div(id='single_sample_figs')]
					  )
			return content
		elif active_tab == 'variants':
			content = [dbc.Row(dbc.Col(id='aa_var_table', width=6), justify='center'),
						dcc.Dropdown(id='select_gene', persistence=True),
						html.Div(id='alignment_fig')
					  ]
			return content



########################################################
###################### LAYOUT ##########################
########################################################

app.layout = dbc.Container(
	fluid=True,
	children=
	[
		#dcc.Store(id='df_cache'),
		#dcc.Store(id='store'),
		html.Div([
			dbc.Row([
				dbc.Col(
						html.Img(
							src=app.get_asset_url('irma-spy.jpg'),
							height=80,
							width=80,
						),
				),
				dbc.Col(
						dcc.Dropdown(id='select_machine',
							options=[{'label':i, 'value':i} for i in sorted(os.listdir(pathway))],
							placeholder='Select sequencing instrument: ',
							persistence=True
						),
				),
				dbc.Col(
						dcc.Dropdown(id='select_run',
							placeholder='Select run directory: ',
						),
				),
				dbc.Col(
						dcc.Dropdown(id='select_irma',
							placeholder='Select IRMA output directory: ',
						),
				)
			]),
		]),
		dbc.Tabs(
			[
				dbc.Tab(label='Demux', tab_id='demux'),
				dbc.Tab(label='IRMA', tab_id='irma'),
				dbc.Tab(label='Variants', tab_id='variants')
			],
			id='tabs',
			active_tab='demux'
		),
		html.Div(id='tab-content')
	]
)

####################################################
####################### MAIN #######################
####################################################
if __name__ == '__main__':
	app.run_server(host= '0.0.0.0', debug=True)
