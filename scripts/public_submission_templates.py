import pandas as pd

user_required_fields_submitter = {
    'NCBI':['NCBI_username', 'NCBI_password', 'First_name', 'Last_name',
            'Email', 'Authors_list'],
    'GISAID':['Client_ID', 'GISAID_username', 'GISAID_password', 'Authors_list']
}

user_required_fields_submission = {
    'FLU':{
        'NCBI':['submission_title', 'collection_date', 'spuid','spuid_namespace',
                'description_title', 'organism_name', 'bioproject', 
                'bs-collected_by', 'bs-collection_date', 'bs-geo_loc_name', 'bs-host',
                'bs-host_disease', 'bs-strain', 'bs-isolation_source', 'bs-lat_lon', 
                'sra-file_location', 'sra-file_path', 'sra-data_type', 'sra-instrument_model',
                'sequence_ID', 'src-collection_date', 'src-country', 'src-host',
                'src-isolation_source'],
        'GISAID':['submission_title', 'collection_date', 'originating_lab_ID', 'isolate_name',
                  'location', 'note', 'originating_lab_id']
    },
    'SC2':{
        'NCBI':['submission_title', 'collection_date', 'spuid','spuid_namespace',
                'description_title', 'organism_name', 'bioproject', 
                'bs-collected_by', 'bs-collection_date', 'bs-geo_loc_name', 'bs-host',
                'bs-host_disease', 'bs-isolate', 'bs-isolation_source',
                'sra-file_location', 'sra-file_path', 'sra-data_type', 'sra-instrument_model',
                'sequence_ID', 'src-collection_date', 'src-country', 'src-host',
                'src-isolation_source', 'src-isolate'],
        'GISAID':['submission_title', 'collection_date', 'originating_lab_ID',
                  'covv_collection_date', 'covv_gender', 'covv_host', 'covv_location',
                  'covv_orig_lab', 'covv_orig_lab_address', 'covv_treatment', 'covv_passage',
                  'covv_patient_age', 'covv_patient_status', 'covv_virus_name']
    }
}

user_optional_fields_submission = {
    'FLU':{
        'NCBI':['bs-host_sex', 'bs-host_age', 'sra-platform', 'sra-loader',
                'src-passage'],
        'GISAID':[]
    },
    'SC2':{
        'NCBI':['bs-host_sex', 'bs-host_age', 'sra-platform', 'sra-loader',
                'src-passage'],
        'GISAID':[]
    }
}

mira_required_fields_submission = {
    'FLU':{
        'NCBI':['organism', 'sra-library_name', 'sra-library_strategy', 'sra-library_source',
                'sra-library_selection', 'sra-library_layout', 'sra-library_construction_protocol',
                'src-strain', 'src-serotype',
                'cmt-StructuredCommentPrefix', 'cmt-Assembly-Method', 'cmt-Coverage',
                'cmt-Sequencing-Technology', 'cmt-StructuredCommentSuffix'],
        'GISAID':['Seq_Id (HA)', 'Seq_Id (HE)', 'Seq_Id (MP)', 'Seq_Id (NA)', 'Seq_Id (NP)',
                  'Seq_Id (NS)', 'Seq_Id (P3)', 'Seq_Id (PA)', 'Seq_Id (PB1)', 'Seq_Id (PB2 )', 'note']
    },
    'SC2':{
        'NCBI':['organism', 'sra-library_name', 'sra-library_strategy', 'sra-library_source',
                'sra-library_selection', 'sra-library_layout', 'sra-library_construction_protocol',
                'src-organism', 'src-organism'],
        'GISAID':['covv_coverage', 'covv_seq_technology', 'covv_virus_name']
    }
}


## Funcitons
def generate_submitter_template_xlsx(u_r_f_s = user_required_fields_submitter):
    df = pd.DataFrame(columns=["Repository","Field","Value"])
    for k,v in u_r_f_s.items():
        for i in v:
            df = df.append({"Repository":k, "Field":i, "Value":""}, ignore_index=True)
    df.to_excel("submitter_config_template.xlsx", index=False, engine='openpyxl')
    return df
