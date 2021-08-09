import pandas as pd
from os.path import dirname, basename, isfile
from glob import glob


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
		df_prime = pd.read_csv(f, sep='\t', index_col=False)
		df_prime.insert(loc=0, column='Sample', value=sample)
		df = df.append(df_prime)
		#for i in args.add_fields_right:
		#	df[i[0]] = i[1]
	return df	
