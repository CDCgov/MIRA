to-do

App.py

    [ ] Amend barcode dropdown for exmpansion packs
    [ ] subsequently change the lib file names
    [ ] Samplesheet 100% backend, no user export, no "-" control
    [ ] Require unique sample names
    [ ] Rename flu segments
    [ ] export all fastas, fastas by sample, fastas by protein, aa fastas
        [ ] exclude QC failures
    [ ] lower coverage threshold
Snake

    [X] Fault tolerance (retries, latency)
        - Wait up to 10 minutes for latency and retry jobs 10 times.[ ] glob for samplesheet with spaces?
    [ ] SC2 WGS
        [ ] will also need to build in custom primer schema configurations
    [ ] Footprint reduction
    [X] Pandas operations to SnakeMake
	    [X] eliminate caching?
            - simplified caching
	    [X] button precedence
            - simplified irma refresh button action
    [ ] Subsampling
        [ ] Assess runtime vs average coverage for various subsampling thresholds for
	        [ ] WGS Illumina Flu
	        [ ] WSG Illumina SC2
	        [ ] Spike Nanopore SC2
	        [ ] WGS Nanopore Flu
	    
        Already tangentially on the docket for SS+me (https://git.biotech.cdc.gov/vfn4/irma/-/issues/23)

    [ ] removal of bbduk for Nanopore
	    [ ] Assess efficiency of minKnow's built-in barcoding removal across sequencing instruments (i.e. does increasing hamming distance cause failed removal or simply failed assignment)
		    [ ] GridION
		    [ ] minION
		    [ ] Mark1C
	    [ ] Secondly, if barcodes are missed, is it moot for flu due to SSW algo?
	    
            - If barcodes are missed in SC2, it cannot be ignored due to hard primer trimming
	        - Pros: speedier, fewer dependencies (JVM build errors avoided)

Documentation

    [ ] documet the wsl2 activation steps in docker desktop
    [ ] if docker run hello world errors out:
        `sudo service docker start`
    [ ] Ensure to open Ubuntu-18.04, not vanilla Ubuntu for computers that have both
    [ ] docker pull not working? sudo
    [ ] containers not showing in docker desktop? resources  --> WSL integration 
    [ ] Docker user groups
    [ ] Turn windows users on/off
    [ ] BIOS
    [ ] sudo chmod -755 /run/docker.sock
    [ ] explain how WSL and Docker eat up memory and to turn off and on as needed https://www.minitool.com/news/vmmem-high-memory.html 

