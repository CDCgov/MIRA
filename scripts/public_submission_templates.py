import pandas as pd

user_required_fields_submitter = {
    'NCBI':['NCBI_username', 'NCBI_password', 'First_name', 'Last_name',
            'Email'],
    'GISAID':['Client_ID', 'GISAID_username', 'GISAID_password'],
    'BOTH':['Authors_list']
}

user_required_fields_submission = {
    'FLU':{
        'NCBI':['spuid','spuid_namespace', 'description_title', 'organism_name', 'bioproject', 
                'bs-collected_by', 'bs-collection_date'; 'bs-geo_loc_name', 'bs-host',
                'bs-host_disease', 'bs-strain', 'bs-isolation_source', 'bs-lat_lon'],
        'GISAID':['Originating_lab_ID'],
        'BOTH':['Submission_title', 'Collection_date',]
    },
    'SC2':{
        'NCBI':['spuid','spuid_namespace', 'description_title', 'organism_name', 'bioproject', 
                'bs-collected_by', 'bs-collection_date'; 'bs-geo_loc_name', 'bs-host',
                'bs-host_disease', 'bs-isolate', 'bs-isolation_source'],
        'GISAID':['Originating_lab_ID'],
        'BOTH':['Submission_title', 'Collection_date',]
    }
}

user_optional_fields_submitter = {
    'FLU':{
        'NCBI':['bs-host_sex', 'bs-host_age'],
        'GISAID':[],
        'BOTH':[]
    },
    'SC2':{
        'NCBI':['bs-host_sex', 'bs-host_age'],
        'GISAID':[],
        'BOTH':[]
    }
}

mira_required_fields_submission = {
    'FLU':{
        'NCBI':['organism'],
        'GISAID':[],
        'BOTH':[]
    },
    'SC2':{
        'NCBI':[],
        'GISAID':[],
        'BOTH':[]
    }
}
