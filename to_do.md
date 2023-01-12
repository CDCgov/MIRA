to-do

App.py

    [ ] Amend barcode dropdown for exmpansion packs --default exp-109...
    [ ] subsequently change the lib file names
    [ ] Samplesheet 100% backend, no user export, no "-" control
    [ ] Require unique sample names
    [ ] Rename flu segments
    [ ] export all fastas, fastas by sample, fastas by protein, aa fastas
        [ ] exclude QC failures
    [ ] lower coverage threshold -- definitely in the line drawn on cov plot; double check irma config
Snake

    [X] Fault tolerance (retries, latency)
        [x] Wait up to 10 minutes for latency and retry jobs 10 times.
        [ ] glob for samplesheet with spaces?
        [ ] unlock folder when launching snakemake -- also kill any running snakemake process first?
    [ ] SC2 WGS -- not needed for Ghana
        [ ] will also need to build in custom primer schema configurations
    [ ] Footprint reduction -- make a separate button? add temp() to snakemake? temp isnt universal solution, ie dont delete IRMA_sample.fin
    [X] Pandas operations to SnakeMake
	    [X] eliminate caching?
            - simplified caching
	    [X] button precedence
            - simplified irma refresh button action
    [ ] Subsampling
        [ ] Assess runtime vs average coverage for various subsampling thresholds for
	        [ ] WGS Illumina Flu
	        [ ] WGS Illumina SC2
	        [X] Spike Nanopore SC2
	        [X] WGS Nanopore Flu

        Already tangentially on the docket for SS+me (https://git.biotech.cdc.gov/vfn4/irma/-/issues/23)

    [ ] removal of bbduk for Nanopore -- Not a viable option yet. We need to really understand other options and do proper experiments.
	    [ ] Assess efficiency of minKnow's built-in barcoding removal across sequencing instruments (i.e. does increasing hamming distance cause failed removal or simply failed assignment)
		    [ ] GridION
		    [ ] minION
		    [ ] Mark1C
	    [ ] Secondly, if barcodes are missed, is it moot for flu due to SSW algo?
	    
            - If barcodes are missed in SC2, it cannot be ignored due to hard primer trimming
	        - Pros: speedier, fewer dependencies (JVM build errors avoided)

Documentation
    [X] documet the wsl2 activation steps in docker desktop
    [X] if docker run hello world errors out:
        `sudo service docker start`
    [X] Ensure to open Ubuntu-18.04, not vanilla Ubuntu for computers that have both
    [X] docker pull not working? sudo
    [X] containers not showing in docker desktop? resources  --> WSL integration 
    [X] Docker user groups
    [X] Turn windows users on/off
    [X] BIOS
    [X] sudo chmod -755 /run/docker.sock


