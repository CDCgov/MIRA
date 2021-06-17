import pandas as pd
from argparse import ArgumentParser as AP
from os.path import realpath, dirname, basename, isfile
from os import stat, remove
from sys import exit
import yaml

def parse_fields(s):
	try:
		h,v = s.split(',')
		return(h,v)
	except:
		raise argparse.ArgumentTypeError("add_fields must be whitespace-seperated list of comma-seperated header,value")


p = AP(description='''Read in text data file(s) and append key-columns''')
r = p.add_argument_group('required arguments')
r.add_argument('-f', '--input_files',  metavar='<inputFiles...>', nargs='+')
r.add_argument('-o', '--output_file', nargs=1)
p.add_argument('-n', '--input_delimiter', help='Default=\'\\t\'', nargs='?', default='\t')
p.add_argument('-u', '--output_delimiter', help='Default=\'\\t\'', nargs='?', default='\t')
p.add_argument('-l', '--add_fields_left', default=[], type=parse_fields, nargs='*',  metavar='<list of header,variable to create additional columns for inputFiles on the LEFT of the dataframe>')
p.add_argument('-r', '--add_fields_right', default=[], type=parse_fields, nargs='*',  metavar='<list of header,variable to create additional columns for inputFiles on the RIGHT of the dataframe>')
p.add_argument('--header', help='Default=False', action='store_true', default=False)

try:
	args = p.parse_args()
except AttributeError:
	p.print_help()
	exit()
if not args.output_file:
	p.print_help()
	exit()

realfiles = []
for f in args.input_files:
	if isfile(f):
		if stat(f).st_size != 0:
			realfiles.append(f)

if isfile(args.output_file[0]):
	print('removing {}'.format(args.output_file[0]))
	remove(args.output_file[0])

for f in realfiles:
	df = pd.read_csv(f, sep=args.input_delimiter, index_col=False)
	for i in args.add_fields_left[::-1]:
		df.insert(loc=0, column=i[0], value=i[1])
	for i in args.add_fields_right:
		df[i[0]] = i[1]
	if isfile(args.output_file[0]):
		df.to_csv(args.output_file[0], sep=args.output_delimiter, index=False, header=False, mode='a+')
	else:
		df.to_csv(args.output_file[0], sep=args.output_delimiter, index=False, header=args.header, mode='a+')
		
