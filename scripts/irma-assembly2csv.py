from subprocess import run
from glob import glob
from sys import argv
from os.path import isdir, basename, realpath, dirname
from tempfile import NamedTemporaryFile
import multiprocessing as mp

# My modules
from muscle import muscle

# Other scripts
alignByPerl = dirname(realpath(__file__))+'/alignPositionByPSA.pl'

nProc = mp.cpu_count()

def id_samples(assemblyPath):
    samples = [basename(i) for i in glob(assemblyPath+'/*') if isdir(i)]
    #print("{} samples identified".format(len(samples)))
    return(samples)

def id_segments(assemblyPath, sample):
    segments = [basename(i).replace('.fasta','') for i in glob('{}/{}/*fasta'.format(assemblyPath, sample))]
    #print("{} segments identified".format(segments))
    return(segments)

def alignConsensus2reference(assemblyPath, sample):
    alignment_dic = {}
    alignment_dic[sample] = {}
    segs = id_segments(assemblyPath, sample)
    
    for seg in segs:
        queryfasta = glob('{}/{}/{}.fasta'.format(assemblyPath, sample, seg))[0]
        reffasta = glob('{}/{}/intermediate/0-ITERATIVE-REFERENCES/R0-{}.ref'.format(assemblyPath, sample, seg))[0]
        alignment_dic[sample][seg] = muscle([reffasta, queryfasta])
    return(alignment_dic)

def alignPositionByPSA(assemblyPath):
    results = []
    for sample in id_samples(assemblyPath):
        for segment, alignment in alignConsensus2reference(assemblyPath, sample)[sample].items():
            covTable = glob('{}/{}/tables/{}-coverage.txt'.format(assemblyPath, sample, segment))[0]
            realignmentFile = dirname(dirname(realpath(__file__)))+'/.cache/'+realpath(assemblyPath).replace('/','_')[1:]+'.csv'            
            header = True
            with open(realignmentFile, 'a+') as out:
                for line in run(['perl', alignByPerl, alignment, covTable], capture_output=True, universal_newlines=True).stdout.split('\n'):
                    if header:
                        l = line.split('\t')
                        l = ['Sample']+[i.replace(' ','_') for i in l]
                        #print(l)
                        header = False
                    else:
                        l = line.split()
                        l = [sample, segment]+l
                    if len(l) > 4:
                        print(','.join(l), file=out)


if __name__ == '__main__':
    try:
        alignPositionByPSA(argv[1])
    except IndexError:
        print("\n\tUSAGE: {} <assemblyPath>\n\n".format(argv[0]))