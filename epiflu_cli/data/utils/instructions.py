#!/usr/bin/env python3

"""
    Upload consensus sequences and metadata to GISAID.
    Copyright (C) 2023 Friends of GISAID.

"""

INSTRUCTIONS = {
"flu": {"Overview": """Fields marked by "**" are required. Every variable type is a string.
Every submission requires at least one segment name,
such as "A/test/Germany/testVIR8728/2023_HA", indicating a
Haemaglutinin segment from Germany with Sample ID testVIR8728
collected in 2023. Missing values leave empty.""",
"Adamantanes_Resistance_geno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Adamantanes_Resistance_pheno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Antigen_Character": "e.g. 'A/Brisbane/10/2007 like'",
"Authors": """Citing authors.
	List of last, first seperated by ;
	E.g.: 'Smith, J.; Jones, D.; Humphries, R.;'""",
"Collection_Date**": """Mandatory.
	At the command line, the default for '--dateformat' correspond to delimited date formats
    consistent with YYYYMMDD. 
    For example:
      - YYYYMMDD corresponds to YYYY-MM-DD, YYYY/MM/DD or YYYY.MM.DD,
      - YYYYDDMM corresponds to YYYY-DD-MM, YYYY/DD/MM or YYYY.DD.MM, etc.
    For other formats, choose the '--dateformat' accordingly.""",
"Collection_Month": """For incomplete collection dates, use this field instead of "Collection_Date".
Month of year:
    "1" = Jan,
	"2" = Feb,
    ...
    "12" = Dec""",
"Collection_Year": """For incomplete collection dates, use this field instead of "Collection_Date".
Four digit year as string:
	e.g. "2023" """,
"Health_Status": """For human hosts:
    Deceased
    Recovered
    In-patient
    Out-patient
    Long-term resident

For animal hosts:
    Healthy
    Sick
    Dead
    """,
"Host": """Host or source name.,
	E.g. 'human', 'avian', 'chicken', 'Anas Acuta', 'environment', etc.""",
"Host_Additional_info": """Any other information about the host or source.""",
"Host_Age": """Age as string, e.g. "15" """,
"Host_Age_Unit": """Unit for the age:
    "Y" for years
    "M" for months
    "D" for days.""",
"Host_Gender": "Alternatives are 'M' or 'F' ",
"Isolate_Id": "Must be empty",
"Isolate_Name**": """Mandatory.
	E.g. 'A/Brisbane/1444A/2010'""",
"Lineage": """"pdm09", "Victoria", "Yamagata" """,
"Location**": """Mandatory.,
	E.g., 'United Kingdom', 'Japan', 'China', 'United States', etc.""",
"Location_Additional_info": "e.g. the city name",
"Note": """A place for any extra notes about the sample. """,
"Originating_Lab_Id": """The numeric ID of the sample's originating laboratory, e.g. "2698". To find this number, run `epiflu_cli labs` (requires authentication).""",
"Originating_Sample_Id": """Internal ID given to the sample by the originating lab.""",
"Oseltamivir_Resistance_geno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Oseltamivir_Resistance_pheno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Other_Resistance_geno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Other_Resistance_pheno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"PMID": """List of PubMed ID's for referencing PubMed records related to the sample.
	Example 1: 1234567
	Example 2: 1234567, 1234568""",
"Passage_History": """E.g. 'Original', 'E2','MX/C1', ... """,
"Peramivir_Resistance_geno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Peramivir_Resistance_pheno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Segment_Ids": """Must be empty String""",
"Seq_Id (HA)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_HA")""",
"Seq_Id (HE)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_HE")""",
"Seq_Id (MP)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_MP")""",
"Seq_Id (NA)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_NA")""",
"Seq_Id (NP)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_NP")""",
"Seq_Id (NS)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_NS")""",
"Seq_Id (P3)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_P3")""",
"Seq_Id (PA)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_PA")""",
"Seq_Id (PB1)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_PB1")""",
"Seq_Id (PB2)": """Name for the Segment (e.g. "A/test/Germany/testVIR8728/2023_PB2")""",
"Submitting_Sample_Id": "Internal ID given to the sample by the submitting lab ",
"Subtype": """e.g. "H5N1" """,
"Zanamivir_Resistance_geno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"Zanamivir_Resistance_pheno": """"Unknown", "Resistant", "Sensitive", "Inconclusive" """,
"province": "Province of the sample location.",
"sub_province": "Sub-Province of the submission location",
}
}
