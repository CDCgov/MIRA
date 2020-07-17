# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from math import ceil
from itertools import cycle

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'IRMA SPY'
df = pd.read_csv(('./test.csv'))

samples = pd.unique(df.Sample)
segments = pd.unique(df.Reference_Name)
segset = [i.split('_')[1] for i in segments]
segset = list(set(segset))

fig_numCols = 4
fig_numRows = ceil(len(samples) / fig_numCols)

pickCol = cycle(list(range(1,fig_numCols+1))) # next(pickCol)
pickRow = cycle(list(range(1, fig_numRows+1))) # next(pickRow)

segcolor = {}
for i in range(0, len(segset)):
	segcolor[segset[i]] = px.colors.qualitative.G10[i] 

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
		df2 = df[(df['Sample'] == s) & (df['Reference_Name'] == g)]
		fig.add_trace(
			go.Scatter(
				x = df2['Position'],
				y = df2['Coverage_Depth'],
				mode = 'lines',
				line = go.scatter.Line(color=segcolor[g_base]),
				name = g
			),
			row = r,
			col = c
		)

fig.update_layout(
	margin=dict(l=0, r=0, t=40, b=0),
	height=1200,
	showlegend=False)


########################################################
###################### LAYOUT ##########################
########################################################

app.layout = html.Div(children=[
	#html.H1(children='IRMA coverage'),
	html.Img(src=app.get_asset_url('irma-spy.jpg'),
			height=50, width=50),

	#html.Div(children='''
	#	Dash: A web application framework for Python.
	#'''),
	#dcc.RadioItems(
	#	options=[

	#	]
	#)
	dcc.Graph(
		id='example-graph',
		figure=fig
	)
])

if __name__ == '__main__':
	app.run_server(debug=True)
