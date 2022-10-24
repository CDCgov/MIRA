import pandas as pd
from os.path import dirname, realpath, basename, isfile
from glob import glob
from re import findall

spath=(realpath(__file__))

def fasta2dic(fasta, dais_ref_format=False):
    seq_dic = {}
    with open(fasta, 'r') as d:
        for line in d.readline():
            if line[0] == '>':
                if dais_ref_format:
                    seq_handle = '|'.join(line[1:].strip().split('|')[:2])
                else:
                    seq_handle = line[1:].strip()
                seq_dic[seq_handle] = ''
            else:
                seq_dic[seq_handle] += line.strip()
    return seq_dic

def run_dais_with_ref(irma_path, dais_executable, references=f'{spath}/data/references/dais_references.fasta', dais_ref_format=True):
    #cat dais_reference seq with irma_path/
    ref_seqs = fasta2dic(references, dais_ref_format)
    amended_consensus_files = glob(f'{irma_path}/*/amended_consensus/*fa')

inscols = ['ID', 'C_type', 'Ref_ID', 'Protein', 'Upstream_aa', 'Inserted_nucleotides', 
        'Inserted_residues', 'Upstream_nt', 'Codon_shift']
inscols_rename = {'ID':'Sample','Ref_ID':'Reference','Protein':'Protein',
        'Upstream_aa':'Upstream AA Position','Inserted_nucleotides':'Inserted Nucleotides',
        'Inserted_residues':'Inserted AAs','Upstream_nt':'Upstream NT','Codon_shift':'In Frame'}
delcols = ['ID', 'C_type', 'Ref_ID', 'Protein', 'VH', 'Del_AA_start', 
        'Del_AA_end', 'Del_AA_len', 'In_frame', 'CDS_ID', 'Del_CDS_start', 
        'Del_CDS_end', 'Del_CDS_len']
delcols_rename = {'ID':'Sample','Ref_ID':'Reference','Protein':'Protein',
        'Del_AA_start':'Del Start AA Position','Del_AA_end':'Del End AA Position',
        'Del_AA_len':'Del AA Length','In_frame':'In Frame',
        'Del_CDS_start':'Del Start CDS Posistion','Del_CDS_end':'Del End CDS Posistion'}
seqcols = ['ID', 'C_type', 'Ref_ID', 'Protein', 'VH', 'AA_seq', 'AA_aln', 'CDS_id', 
        'Insertion', 'Shift_Insert', 'CDS_seq', 'CDS_aln', 'Query_nt_coordinates', 
        'CDS_nt_coordinates']
seqcols_rename = {'ID':'Sample','Ref_ID':'Reference','Protein':'Protein', 'AA_seq':'AA Sequence',
        'AA_aln':'Aligned AA Sequence','Insertion':'Insertion','Shift_Insert':'Insertion Shifts Frame',
        'CDS_seq':'CDS Sequence','CDS_aln':'Aligned CDS Sequence',
        'Query_nt_coordinates':'Reference NT Positions','CDS_nt_coordinates':'Sample NT Positions'}

def dais2df(results_path, colnames, col_renames, dais_suffix, full=False):
    files = glob(f'*{dais_suffix}')
    df = pd.DataFrame()
    for f in files:
        df = df.append(pd.read_csv(f, sep='\t', names=colnames))
    if full:
        return df
    else:
        df = df[col_renames.keys()]
        df = df.rename(columns=col_renames)
        return df

def dels_df(results_path):
    return dais2df(results_path, delcols, delcols_rename, '.del')

def ins_df(results_path):
    return dais2df(results_path, inscols, inscols_rename, '.ins')

def seq_df(results_path):
    return dais2df(results_path, seqcols, seqcols_rename, '.seq')

'''original app effort functions. Possibly useful for printing out AA fastas
def dais2fasta(dais_seq_file, outpath='.'):
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
'''