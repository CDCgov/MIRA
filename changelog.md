#### v1.0.1
- looks for samplesheet with case insensitive matching of glob(data/run/*csv) items containing "samplesheet" or "data"
- removes carriage return: ^M from samplesheet which occurs when user copy and pastes sample IDs from excel into SPY's samplesheet creator.
- NEED TO add refresh to list runs...