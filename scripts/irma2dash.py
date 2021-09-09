import pandas as pd
from os.path import dirname, basename, isfile
from glob import glob
import plotly.express as px
from re import findall
import plotly.graph_objects as go

def seg(s):
	return findall(r'HA|NA|MP|NP|NS|PA|PB1|PB2|SARS-CoV-2',s) 

def returnStageColors(df):
	df = df[df['Stage'].isin([4,5])]
	recs = list(set([seg(i)[0] for i in list(df['Record'])]))
	reccolor = {}
	for i in range(0, len(recs)):
		reccolor[recs[i]] = px.colors.qualitative.G10[i]
	return reccolor

def dash_reads_to_sankey(df):
	df = df[df['Stage'] != 0]
	reccolor = returnStageColors(df)
	labels = list(df['Record'])
	x_pos, y_pos, color = [], [], []
	for i in labels:
		if i[0] == '1':
			x_pos.append(0.05)
			y_pos.append(0.1)
			color.append('#8A8A8A')
		elif i[0] == '2':
			x_pos.append(0.2)
			y_pos.append(0.1)
			color.append('#8A8A8A')
		elif i[0] == '3':
			x_pos.append(0.35)
			y_pos.append(0.1)
			color.append('#8A8A8A')
		else:
			x_pos.append(0.95)
			y_pos.append(0.01)
			color.append(reccolor[seg(i)[0]])
	source, target, value= [], [], []
	for index, row in df.iterrows():
		if row['Stage'] == 4 or row['Stage'] == 5:
			source.append(labels.index('3-match'))
			target.append(labels.index(row['Record'])) 
			value.append(row['Reads'])
		elif row['Stage'] == 3:
			source.append(labels.index('2-passQC'))
			target.append(labels.index(row['Record'])) 
			value.append(row['Reads'])
		elif row['Stage'] == 2:
			source.append(labels.index('1-initial')) 
			target.append(labels.index(row['Record']))
			value.append(row['Reads'])
	fig = go.Figure(data=[go.Sankey(
		arrangement='snap',
		node = dict(
		  pad = 15,
		  thickness = 20,
		  label = labels,
		  x = x_pos,
		  y = y_pos,
		  color = color,
		  hovertemplate = '%{label} %{value} reads <extra></extra>'
		),
		link = dict(
		  source = source, 
		  target = target,
		  value = value,
		  color = color[1:],
		  hovertemplate = '<extra></extra>'
	  ))])
	return fig

def dash_irma_reads_df(irma_path):
	if isfile(irma_path+'/reads.parquet'):
		df = pd.read_parquet(irma_path+'/reads.parquet')
		return df
	readFiles = glob(irma_path+'/*/tables/READ_COUNTS.txt')
	df = pd.DataFrame()
	for f in readFiles:
		sample = basename(dirname(dirname(f)))
		df_prime = pd.read_csv(f, sep='\t', index_col=False)
		df_prime.insert(loc=0, column='Sample', value=sample)
		df = df.append(df_prime)
	df['Stage'] = df['Record'].apply(lambda x: int(x.split('-')[0]))
	df.to_parquet(irma_path+'/reads.parquet')
	return df	

def dash_irma_coverage_df(irma_path):
	if isfile(irma_path+'/coverage.parquet'):
		df = pd.read_parquet(irma_path+'/coverage.parquet')
		return df
	coverageFiles = glob(irma_path+'/*/tables/*a2m.txt')
	a2msamples = [i.split('/')[-3] for i in coverageFiles]
	otherFiles = [i for i in glob(irma_path+'/*/tables/*coverage.txt')]
	if len(coverageFiles) == 0:
		coverageFiles = glob(irma_path+'/*/tables/*coverage.txt')
	if len(coverageFiles) == 0:
		return 'No coverage files found under {}/*/tables/'.format(irma_path)
	df = pd.DataFrame()
	for f in coverageFiles:
		sample = basename(dirname(dirname(f)))
		print(sample, f)
		df_prime = pd.read_csv(f, sep='\t', index_col=False)
		df_prime.insert(loc=0, column='Sample', value=sample)
		df = df.append(df_prime)
		#for i in args.add_fields_right:
		#	df[i[0]] = i[1]
	df.to_parquet(irma_path+'/coverage.parquet')
	return df	
