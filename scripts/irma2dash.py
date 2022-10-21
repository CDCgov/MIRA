from pickletools import read_decimalnl_short
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

def irmatable2df(irmaFiles):
	df = pd.DataFrame()
	for f in irmaFiles:
		sample = basename(dirname(dirname(f)))
		df_prime = pd.read_csv(f, sep='\t', index_col=False)
		df_prime.insert(loc=0, column='Sample', value=sample)
		df = df.append(df_prime)
	return df

def dash_irma_reads_df(irma_path):
	if isfile(irma_path+'/reads.csv.gz'):
		df = pd.read_csv(irma_path+'/reads.csv.gz')
		return df
	readFiles = glob(irma_path+'/*/tables/READ_COUNTS.txt')
	df = pd.DataFrame()
	df = irmatable2df(readFiles)
	df['Stage'] = df['Record'].apply(lambda x: int(x.split('-')[0]))
	df.to_csv(irma_path+'/reads.csv.gz', compression='gzip')
	return df	

def dash_irma_coverage_df(irma_path):
	if isfile(irma_path+'/coverage.csv.gz'):
		df = pd.read_csv(irma_path+'/coverage.csv.gz')
		return df
	coverageFiles = glob(irma_path+'/*/tables/*a2m.txt')
	#a2msamples = [i.split('/')[-3] for i in coverageFiles]
	#otherFiles = [i for i in glob(irma_path+'/*/tables/*coverage.txt')]
	if len(coverageFiles) == 0:
		coverageFiles = glob(irma_path+'/*/tables/*coverage.txt')
	if len(coverageFiles) == 0:
		return 'No coverage files found under {}/*/tables/'.format(irma_path)
	df = irmatable2df(coverageFiles)
	df.to_csv(irma_path+'/coverage.csv.gz', compression='gzip')
	return df

def dash_irma_alleles_df(irma_path, full=False):
	if isfile(irma_path+'/alleles.csv.gz'):
		df = pd.read_csv(irma_path+'/alleles.csv.gz')
		df = df.loc[:,df.columns!='Unnamed: 0']
		return df
	alleleFiles = glob(irma_path+'/*/tables/*variants.txt')
	df = irmatable2df(alleleFiles)
	if not full:
		if 'HMM_Position' in df.columns:
			ref_heads = ['Sample', 'Reference_Name', 'HMM_Position', 
			'Position', 'Total', 'Consensus_Allele', 'Minority_Allele', 
			'Consensus_Count', 'Minority_Count', 'Minority_Frequency']
		else:
			ref_heads = ['Sample', 
			'Position', 'Total', 'Consensus_Allele', 'Minority_Allele', 
			'Consensus_Count', 'Minority_Count', 'Minority_Frequency']
		df = df[ref_heads]
		df = df.rename(columns={'Reference_Name':'Reference', 'HMM_Position':'Reference Position', 
					'Position':'Sample Position', 'Total':'Coverage', 'Consensus_Allele':'Consensus Allele', 
					'Minority_Allele':'Minority Allele', 'Consensus_Count':'Consensus Count', 
					'Minority_Count':'Minority Count', 'Minority_Frequency':'Minority Frequency'})
	df.to_csv(irma_path+'/alleles.csv.gz', compression='gzip')
	return df

def dash_irma_indels_df(irma_path, full=False):
	if isfile(irma_path+'/indels.csv.gz'):
		df = read_csv(irma_path+'/indels.csv.gz')
		return df
	insertionFiles = glob(irma_path+'/*/tables/*insertions.txt')
	deletionFiles = glob(irma_path+'/*/tables/*deletions.txt')
	idf = irmatable2df(insertionFiles)
	ddf = irmatable2df(deletionFiles)
	df = pd.concat([idf,ddf])
	if 'HMM_Position' in df.columns:
		df = df.rename(columns={'Reference_Name':'Reference', 
					'Upstream_Position':'Sample - Upstream Position', 
					'HMM_Position':'Reference - Upstream Position',
					'Total':'Upstream Base Coverage'})
		df = df[['Sample', 'Sample - Upstream Position', 'Reference', 
		'Reference - Upstream Position', 'Context', 'Length', 
		'Insert', 'Count', 'Upstream Base Coverage', 'Frequency']]
	else:
		df = df.rename(columns={'Reference_Name':'Reference', 
					'Upstream_Position':'Sample - Upstream Position', 
					'Total':'Upstream Base Coverage'})
		df = df[['Sample', 'Sample - Upstream Position', 'Reference', 
		 'Context', 'Length', 
		'Insert', 'Count', 'Upstream Base Coverage', 'Frequency']]
	return df

def reference_lens(irma_path):
	reffiles = glob(irma_path+'/*/intermediate/0-ITERATIVE-REFERENCES/R0*ref')
	ref_lens = {}
	for f in reffiles:
		ref = basename(f)[3:-4]
		if ref not in ref_lens.keys():
			with open(f, 'r') as d:
				seq = ''
				for line in d:
					if not line[0] == '>':
						seq += line.strip()
			ref_lens[ref] = len(seq)
	return ref_lens					
