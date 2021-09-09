#!/usr/bin/env python
from sys import argv

def dais2fasta(daisfile, outpath='.'):
	seqs = {}
	with open(daisfile, 'r') as d:
		for line in d:
			l = line.split()
			if l[4] != '\\N':
				#sample = l[0]
				sample, reference, gene, seq_id, seq = l[0], *l[2:5], l[6]
				try:
					seqs[sample][gene] = {'reference':reference, 'seq_id':seq_id, 'seq':seq}
				except:
					seqs[sample] = {gene : {'reference':reference, 'seq_id':seq_id, 'seq':seq}}
	for sample, dic in seqs.items():
		for gene, data in dic.items(): 
			with open('{}/{}.fasta'.format(outpath, gene), 'a+') as out:
				print('>{}_{}'.format(sample, gene), file=out)
				print(data['seq'], file=out)
	return seqs

def seqs2table(seqs, reference, outpath='.'):
	with open('{}/AAvariants.txt'.format(outpath), 'w') as out:
		print('\t'.join(['Gene', 'AA Position', 'Reference', 'Reference AA', 'Sample', 'Sample AA']), file=out)
		for sample,dic in seqs.items():
			for gene, data in dic.items():
				if sample != reference:
					try:
						pos = 1
						for r,q in zip(seqs[reference][gene]['seq'],seqs[sample][gene]['seq']):
							if r != q:	
								print('\t'.join([gene, str(pos), reference, r, sample, q]), file=out)
							pos += 1
					except KeyError:
						pass

if __name__ == '__main__':
	print('Producing fasta files from {}'.format(argv[1]))
	seqs2table(dais2fasta(argv[1]), argv[2])
	print('Finished')
