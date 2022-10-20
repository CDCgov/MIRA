import yaml
from os.path import abspath
from sys import argv, exit
import pandas as pd
from glob import glob
import subprocess

root = '/'.join(abspath(__file__).split('/')[:-2])

if len(argv) < 1:
        exit('\n\tUSAGE: {} <samplesheet.csv> <runpath> \n'.format(__file__))

try:
        runpath = argv[2]
except (IndexError, ValueError):
        runid = 'testRunID'

data = {'runid':runpath.split('/')[runpath.split('/').index('fastq_pass') -1], 'barcodes':{}}
def reverse_complement(seq):
    rev = {'A':'T','T':'A','C':'G','G':'C',',':','}
    seq = seq[::-1]
    return ''.join(rev[i] for i in seq)


df = pd.read_csv(argv[1])
dfd = df.to_dict('index')
failures = ''
try:
    with open('{}/lib/{}.yaml'.format(root, dfd[0]['Barcode Expansion Pack']), 'r') as y:
        barseqs = yaml.safe_load(y)
except:
    with open('{}/lib/{}.yaml'.format(root, dfd[0]['Barcode Expansion Pack']), 'r') as y:
        barseqs = yaml.safe_load(y)
for d in dfd.values():
    fastq_pass = glob(runpath + '/*/')
    if d['Barcode #'] in [x.split("/")[-2] for x in fastq_pass]:

        data['barcodes'][d['Sample ID']] = {
                                                                        
                                                                        'sample_type':d['Sample Type'],
                                                                        'barcode_number':d['Barcode #'],
                                                                        'barcode_sequence':barseqs[d['Barcode #']],
                                                                        'barcode_sequence_rc':reverse_complement(barseqs[d['Barcode #']])}
    else:
        failures += str(d['Barcode #']) + '\n'
with open('config.yaml', 'w') as out:
        yaml.dump(data, out, default_flow_style=False)

if len(failures) > 1:
    print("failed samples detected: Barcodes\n",failures.strip() )
