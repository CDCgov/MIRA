import os
import pickle
from re import search

root = '/scicomp/groups/OID/NCIRD/ID-OD/ISA/by-instrument'

# Build a nested dictionary of IRMA_assemblies[machine][run][assemblies]
def removeDirList(dirs, rmlist):
    #for i in rmlist:
    dirs_rm = [i for i in dirs for j in rmlist if search(j,i)]
    return dirs_rm

def find_assemblies(path):
	IRMA_assemblies = {}
	rmlist = ['fast[q5]', 'guppy-\d-\d-\d+$', 'albacore-\d-\d-\d+$', 'albacore-\d-\d-\d+_v*', 
                    'barcode', 'unclassified', 'discover', 'mux_scan', 'timecourse', 'quick', 
                    'Project', 'Basecall', 'Temp', 'Reports', 'curation', 'BAD', 'surveillance',
                    '^1[4567]\d\d\d\d_M', 'IGT', 'ISA', '[eE]rror']
	for root, dirs, files, in os.walk(path):
		dirs_rm = removeDirList(dirs, rmlist)
		for i in dirs_rm:
			#print("rm="+i)
			try:
				dirs.remove(i)
			except ValueError:
				pass
		for i in dirs:
			print(root, i)
			if search('^assemblies', i):
				dirs.remove(i)
				fullpath = os.path.realpath(root+'/'+i)
				machine, runID = fullpath.split('/')[8:10]
				assembly = '/'.join(fullpath.split('/')[10:])
				#print("machine={}\trunID={}\tassembly={}\n".format(machine, runID, assembly))
				try:
					IRMA_assemblies[machine][runID].append(assembly)
				except:
					try:
						IRMA_assemblies[machine][runID] = [assembly]
					except:
						IRMA_assemblies[machine] = {runID : [assembly]}
	return(IRMA_assemblies)
        

if __name__ == '__main__':
	dataDic = find_assemblies(root)
	pklfile = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+'/cache-data/irma_assemblies.pkl'
	with open(pklfile, 'wb') as d:
		pickle.dump(dataDic, d)
