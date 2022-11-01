#!/usr/bin/python3

import fileinput
from tempfile import NamedTemporaryFile
from subprocess import run
from os.path import realpath, dirname, isfile

def muscle(fasta):
	'''Provided a list of fasta files, a single fasta file with multiple sequences,
	or a dicitonary of key=SeqIDs:values=Sequences, returns a temporary file handle
	containing a muscle alignment.'''

	if not fasta:
		print("\n\nSequences required. Duh.\n\n")
		return

	MUSCLE = '/'.join(realpath(__file__).split('/')[:-2]+['bin','muscle3.8.31_i86linux64'])
	
	tmp_unaligned = NamedTemporaryFile('a+', delete=False)
	tmp_aligned = NamedTemporaryFile('a+', delete=False)
	tmp_aligned.close()

	if isfile(list(fasta)[0]):
		with fileinput.FileInput(tuple(fasta)) as reffastas:
			for line in reffastas:
				tmp_unaligned.write(line)
	elif 'dict' in str(type(fasta)):
		for i,s in fasta.items():
			if i[0] == '>':
				tmp_unaligned.write(i+'\n')
			else:
				tmp_unaligned.write('>'+i+'\n')
			tmp_unaligned.write(s+'\n')
	else:
		print("\n\n<fasta> not a file, list of files, or dictionary of seqs\n\n")
		return
	tmp_unaligned.close()
	run([MUSCLE, '-quiet', '-in', tmp_unaligned.name, '-out', tmp_aligned.name], universal_newlines=True)
	return tmp_aligned.name

if __name__ == '__main__':
	from sys import argv
	muscle(argv)
