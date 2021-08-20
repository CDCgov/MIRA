import pandas as pd
from os.path import dirname, basename, isfile
from glob import glob

def dash_reads_to_sankey(reads_df):
	labels = list(df['Record'])
	x_pos = []
	y_pos = []
	x_dic = {'0':0,'1':0.2,'2':0.4,'3':0.6, '4':0.8, '5':0.8}
	for i in labels:
		x_pos.append(x_dic[i[0]])
		y_pos.append(0.5)
	label_dic = {}
	for i in range(0,len(labels)):
		label_dic[labels[i]] = i
	source, target, value = [], [], []
	for index, row in df.iterrows():
		if row['Stage'] == 4 or row['Stage'] == 5:
			source.append(label_dic['3-match'])
			target.append(label_dic[row['Record']])
			value.append(row['Reads'])
	for index, row in df.iterrows():
		if row['Stage'] == 3:
			source.append(label_dic['2-passQC'])
			target.append(label_dic[row['Record']])
			value.append(row['Reads'])
	for index, row in df.iterrows():
		if row['Stage'] == 2:
			source.append(label_dic['1-initial'])
			target.append(label_dic[row['Record']])
			value.append(row['Reads'])
	fig = go.Figure(data=[go.Sankey(
		arrangement='snap',
		node = dict(
		  pad = 15,
		  thickness = 20,
		  line = dict(color = "black", width = 0.5),
		  label = labels,
		  x = x_pos,
		  y = y_pos,
		  color = "blue"
		),
		link = dict(
		  source = source, 
		  target = target,
		  value = value
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
