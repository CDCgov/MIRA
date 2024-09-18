

# <img src="man/figures/logo.png" align="left" width="190" /> MIRA: Interactive Dashboard for Influenza, SARS-CoV-2 and RSV Assembly and Curation

![pkgdown](https://github.com/cdcgov/mira/workflows/pkgdown/badge.svg)
![Docker pulls](https://img.shields.io/docker/pulls/cdcgov/mira)
![Docker image size](https://img.shields.io/docker/image-size/cdcgov/mira) 
![GitHub last commit](https://img.shields.io/github/last-commit/cdcgov/mira)

<br>

**General disclaimer** This repository was created for use by CDC
programs to collaborate on public health related projects in support of
the [CDC mission](https://www.cdc.gov/about/divisions-offices/index.html).
GitHub is not hosted by the CDC, but is a third party website used by
CDC and its partners to share information and collaborate on software.
CDC use of GitHub does not imply an endorsement of any one particular
service, product, or enterprise.

<hr>
<br>

# Overview

**MIRA** is a bioinformatics pipeline that assembles Influenza genomes, SARS-CoV-2 genomes, the SARS-CoV-2 spike-gene and RSV genomes when given the raw fastq files and a samplesheet. MIRA can analyze reads from both Illumina and OxFord Nanopore sequencing machines. Coming soon, it
will allow for upload via FTP to NCBI’s databases
**Genbank**, **BioSample**, and **SRA**, as well as **GISAID**.

![](man/figures/MIRA_flowchart_pptx.png)

<hr>

## Which MIRA is right for you?


### Running MIRA with Docker Desktop
MIRA-GUI is run on a local computer. It is ideal for users who are not familiar with using the command line, but would still like to perform genomic analysis and render quality figures. 

Computational Requirements:

- A minimum of 16GB of memory is required. >=32GB is recommended.
- A minimum of 8 CPU cores. 16 are recommended.

Skill Needed:

- Understanding of fastq files and their file structure.

Key features:

- GUI web interface

To run MIRA with Docker Desktop you can get started [here]().

### Running MIRA-CLI with Docker
MIRA-CLI is ran on a local computer in the command line. It is ideal for users who are familiar with using the command line and would like to perform genomic analysis and render quality figures. 

Computational Requirements: 

- A minimum of 16GB of memory is required. >=32GB is recommended.
- A minimum of 8 CPU cores. 16 are recommended.
- **Administrative privileges are required on a Windows operating system _to run linux_.**
- A linux/unix (includes Intel-based* MacOS) operating system is required.
    - *This software has not yet been tested on Apple's M-chip based OS
    - If you are using a Mac, [go to Mac Getting Started.](mira-cli-mac-getting-started.htmll)

Skill Needed:

- Familiarity with command line interface.
- Understanding of fastq files and their file structure.

Key features:

- HTML reports

To run MIRA-CLI you can get started with our [PC instructions](getting-started.html) or [Mac instructions](mira-cli-mac-getting-started.html) .

### Running MIRA-NF with Nextflow
MIRA-NF is ran on a high performing computing (HPC) cluster or in a cloud computing platform. It is ideal for users who are familiar with using the command line, familiar with high computing clusters and would like to perform genomic analysis and render quality figures. 

Computational Requirements:

- Access to an HPC or cloud computing platform.

Skill Needed:

- Familiarity with analyzing data in HPC and cloud computing platforms. 
- Strong understanding of command line interface.
- Understanding of fastq files and their file structure.

Key features:

- Able to run large data sets without the need for subsampling
- HTML reports

To run MIRA-NF you can get started [here](https://github.com/CDCgov/MIRA-NF).

<hr>

## Test your MIRA Setup
    
- [Click here to download tiny test data from ONT Influenza genome and SARS-CoV-2-spike - 40Mb](https://centersfordiseasecontrol.sharefile.com/d-s839d7319e9b04e2baba07b4d328f02c2)
- [Click here for the above data set + full genomes of Influenza and SARS-CoV-2 from Illumina MiSeqs - 1Gb](https://centersfordiseasecontrol.sharefile.com/d-s3c52c0b25c2243078f506d60bd787c62)
- unzip the file and find two folders:
    1. `tiny_test_run_flu`
    2. `tiny_test_run_sc2`
- move these folders into `FLU_SC2_SEQUENCING`
  - if you cannot find the FLU_SC2_SEQUENCING folder in your Linux section of file explorer, look in Linux-->home-->your username

- Open your browser and type http://localhost:8020 in the address bar.
- Click `Refresh Run Listing` in MIRA, you should now see these folders listed.
- Click `Download Samplesheet`.
  - This will give you an excel sheet with available barcodes populated. Add in our samplenames for ONT data (Illumina data will self identify samplenames based on fastqs)
- Save the samplesheet and then upload it by clicking on `Drag and Drop your Samplesheet or Click and Select the File`
- In the dropdown box 'What kind of data is this?', select the correct data type.
  - If SC2 full genome, also select your primers.
- Click 'START GENOME ASSEMBLY'
- Toggle 'Watch IRMA progress' to see IRMA's stdout stream.
- When "IRMA is finished!" is displayed,  Click "DISPLAY IRMA RESULTS"


<hr>

