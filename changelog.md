#### v1.0.1
- looks for samplesheet with case insensitive matching of glob(data/run/*csv) items containing "samplesheet" or "data"
- removes carriage return: ^M from samplesheet which occurs when user copy and pastes sample IDs from excel into SPY's samplesheet creator.
- Button added to refresh run listing
- Downloaded fasta for FLU now changes the flu segment numbers to the gene name
- TO DO: REDUCE DAIS RESULT TABLE FOR FLU TO FULL PROTEINS, (ie remove ha signal, etc....)