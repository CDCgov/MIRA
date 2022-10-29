import yaml
from os.path import abspath
from sys import argv, exit
import pandas as pd
from glob import glob
import subprocess
import os

root = "/".join(abspath(__file__).split("/")[:-2])

if len(argv) < 1:
    exit(
        "\n\tUSAGE: {} <samplesheet.csv> <runpath> <experiment_type>\n".format(__file__)
    )

try:
    runpath = argv[2]
    experiment_type = argv[3]
except (IndexError, ValueError):
    runid = "testRunID"
df = pd.read_csv(argv[1])
dfd = df.to_dict("index")

if 'ont' in experiment_type.lower():
    if 'fastq_pass' in runpath:
        data = {'runid':runpath.split('/')[runpath.split('/').index('fastq_pass') -1], 'barcodes':{}}
    else:
        data = {'runid':runpath, 'barcodes':{}}
    def reverse_complement(seq):
        rev = {"A": "T", "T": "A", "C": "G", "G": "C", ",": ","}
        seq = seq[::-1]
        return "".join(rev[i] for i in seq)

    failures = ""
    try:
        with open(
            "{}/lib/{}.yaml".format(root, dfd[0]["Barcode Expansion Pack"]), "r"
        ) as y:
            barseqs = yaml.safe_load(y)
    except:
        with open(
            "{}/lib/{}.yaml".format(root, dfd[0]["Barcode Expansion Pack"]), "r"
        ) as y:
            barseqs = yaml.safe_load(y)
    for d in dfd.values():
        if 'fastq_pass' in runpath:
            fastq_pass = glob(runpath + '/*/')
        else:
            fastq_pass = glob(runpath + '/fastq_pass/*/')
        if d['Barcode #'] in [x.split("/")[-2] for x in fastq_pass]:

            data["barcodes"][d["Sample ID"]] = {
                "sample_type": d["Sample Type"],
                "barcode_number": d["Barcode #"],
                "barcode_sequence": barseqs[d["Barcode #"]],
                "barcode_sequence_rc": reverse_complement(barseqs[d["Barcode #"]]),
            }
        else:
            failures += str(d["Barcode #"]) + "\n"

    if len(failures) > 1:
        print("failed samples detected: Barcodes\n", failures.strip())
else:
    data = {'runid':runpath, 'samples':{}}
    for d in dfd.values():
        data["samples"][d["Sample ID"]] = {
                "sample_type": d["Sample Type"]
            }
with open(runpath.replace("fastq_pass", "") + "/config.yaml", "w") as out:
    yaml.dump(data, out, default_flow_style=False)

snakefile_path = f"{root}/../SC2-spike-seq/workflow/"
if "ont" in experiment_type.lower():

    if "flu" in experiment_type.lower():
        snakefile_path += "influenza_snakefile"
    elif "sc2" in experiment_type.lower():
        snakefile_path += "sc2_spike_snakefile"
else:
    snakefile_path += "illumina_influenza_snakefile"
snake_cmd = (
        "snakemake -s " + snakefile_path + " --configfile config.yaml --cores 4 "
    )
os.chdir(runpath.replace("fastq_pass", ""))
subprocess.call(snake_cmd, shell=True)

