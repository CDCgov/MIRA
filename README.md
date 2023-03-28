
# MIRA: Interactive Dashboard for Influenza Genome and SARS-CoV-2 Spike-Gene Assembly and Curation

Version: 1.0.0 (Beta)

**Beta version** This pipeline is currently in Beta testing and issues
could appear during submission, use at your own risk. Feedback and
suggestions are welcome!

**General disclaimer** This repository was created for use by CDC
programs to collaborate on public health related projects in support of
the [CDC mission](https://www.cdc.gov/about/organization/mission.htm).
GitHub is not hosted by the CDC, but is a third party website used by
CDC and its partners to share information and collaborate on software.
CDC use of GitHub does not imply an endorsement of any one particular
service, product, or enterprise.

<hr>
<br>

## **Documentation: [https://CDCgov.github.io/MIRA/](https://CDCgov.github.io/MIRA/)**

<br>

# Overview

**MIRA** is an interactive dashboard created using **[Dash](https://dash.plotly.com/introduction)**, a python framework
written on the top of **Flask**, **Plotly.js** and **React.js**. The dashboard
allows users to interactively create a metadata and config file for
running Influenza Genome and SARS-CoV-2 Spike-Gene Assembly. Coming soon, it
will allow for upload via FTP to NCBI’s databases
**Genbank**, **BioSample**, and **SRA**, as well as **GISAID**.


MIRA’s dashboard relies on four Docker containers to run its genome assembly and curation: 

- **IRMA (Iterative Refinement Meta-Assembler):** designed for the robust assembly, variant calling, and phasing of highly variable RNA viruses. IRMA is deployed with modules for influenza, ebolavirus and coronavirus.
- **DAIS-Ribosome:** compartmentalizes the translation engine developed for the CDC Influenza Division protein analytics database. The tool has been extended for use with Betacoronavirus.
- **spyne:** a Snakemake workflow manager designed for running Influenza Genome and SARS-CoV-2 Spike-Gene assembly.
- **MIRA:** a GUI web interface that allows users to interactively create a metadata and config file for running Influenza Genome and SARS-CoV-2 Spike-Gene assembly and curation.

![](man/figures/mira_flowchart_mermaid.png)

<hr>

## Quick Start on Ubuntu OS:
- <a href="https://raw.githubusercontent.com/CDCgov/MIRA/prod/MIRA-INSTALL.sh" download>Right click this link and click 'save as'</a> and save it into the folder that you will add new run-folders to, ie. `FLU_SC2_SEQUENCING`.
- Navigate to that folder on the command line and run:
    ```
    chmod +x ./MIRA-INSTALL.sh
    ```
- Run the install script with sudo:
    ```
    sudo ./MIRA-INSTALL.sh
    ```
- [Click here to download test data](https://centersfordiseasecontrol.sharefile.com/d-sb2d3b06e9ef946cf89e1a43c5a141a3f)
- unzip the file and find two folders:
    1. `tiny_test_run_flu`
    2. `tiny_test_run_sc2`
- move these folders into `FLU_SC2_SEQUENCING`

- Open your browser and type http://localhost:8020 in the address bar.
- Click `Refresh Run Listing` in MIRA, you should now see these folders listed.
- Select "tiny_test_run_flu", enter barcode numbers `27,37,41` and make up sample names.
  - Click 'SAVE SAMPLESHEET'
  - In the dropdown box 'What kind of data is this?', select 'Flu-ONT'
  - Click 'START GENOME ASSEMBLY'
  - Toggle 'Watch IRMA progress' to see IRMA's stdout stream.
  - When "IRMA is finished!" is displayed,  Click "DISPLAY IRMA RESULTS"
- Now select "tiny_test_run_sc2" from the very top dropdown and repeat the above steps except this time enter barcode numbers `2,3,5,8,28`.
    
<hr>
