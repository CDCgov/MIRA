
# MIRA 1.1.2
* Github Repo: https://github.com/CDCgov/MIRA
* Documentation: https://cdcgov.github.io/MIRA

### v1.1.2
- Whole-Genome SC2 Nanopore module
- Illumina 2x75 support
- Java instability fixed
- New Version Checking
- Lab protocols published on documentation website
- Docker compose steps added to quickstart on documentation website
- Quality control checks for S-gene specific metrics added to Whole-Genome SC2 modules
- IRMA container V1.1.1
- Final amended .bams included in tarball
  
#### v1.1.1
- Pandas version --> 1.1.0
- Mac docs updated to show Rosetta usage in Docker Desktop
- More thorough error and status messaging during assembly

#### v1.1.0
- Illumina sequencing for WGS SC2 and Flu
- Auto-samplesheet building
- Samplesheet download/upload functionality
- Button added to refresh run listing
- Button added to download failed fastas
- Downloaded fasta for FLU now changes the flu segment numbers to the gene name
- Allow numeric samplenames, and allow "-" in sample names
- Toss broken reads for ONT fastqs
- Return only closer Flu B reference in amino acid variants table
- Better error handling for empty/failed nanopore barcodes
- Indel table filtered to >20%, Minor variant table filtered to >5%
- Archive previous run logs in the even of a re-run

