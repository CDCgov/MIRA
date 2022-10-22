# irma-spy

1. Clone repo
   
    ```bash
    git clone git@git.biotech.cdc.gov:nbx0/irma-spy.git
    ```
2. Build and activate conda environment
    ```bash
    conda env create --force -f config/snakemake_environment.yml
    conda activate irma-spy
    ```
3. Launch app and view in your browser at http://localhost:8050/
    ```bash
    python app.py
    ```
