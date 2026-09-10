# Import future annotations for Pydantic models
from __future__ import annotations
import os
from threading import Lock
from typing import List, Optional, Literal, Dict, Any, Tuple

# Import polars
import polars as pl

# Import general python packages
import yaml
import subprocess

# Import shared logger (INFO/DEBUG -> stdout, WARNING/ERROR/CRITICAL -> stderr)
from .logging_config import logger

# Import local schema modules
from .schema_validator import (
    _DEFAULT_SEQSENDER_STORAGE_PATH,
    CONFIG_FILENAME,
    METADATA_FILENAME,
    FASTA_FILENAME,
    GFF_FILENAME,
    TABLE2ASN_FILENAME,
    SUBMISSION_LOG_FILENAME,
    SUBMISSION_STATUS_REPORT_FILENAME,
    CONFIG_TEMPLATE_PATH,
    validate_tbl,
    biosample_packages,
    submitter_db_schema,
    submitter_pa_schema,
    submission_db_schema,
    submission_pa_schema,
)

# Import local sqlite modules
from .sqlite_handler import (
    lookup_tbl_in_database,
    insert_tbl_to_database,
    update_tbl_in_database,
)

# Import local utils
from .utils import (
    _cast_expr,
    compare_and_update_db_table,
)

# Global dictionaries and lock for managing SeqSender processes and their terminal results.
_SEQSENDER_PROCESSES: Dict[int, Dict[str, Any]] = {}
_SEQSENDER_TERMINAL_RESULTS: Dict[int, Dict[str, Any]] = {}
_SEQSENDER_PROCESS_LOCK = Lock()
_MAX_TERMINAL_RESULTS = 256


def _seqsender_process_identity(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
) -> Tuple[str, str, Tuple[str, ...], str]:
    return submission_name, organism, tuple(sorted(database)), submission_type


def _update_seqsender_submission_status(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
    status: str,
) -> None:
    for target_database in database:
        target_submission_type = "PRODUCTION" if target_database == "GISAID" else submission_type
        update_tbl_in_database(
            db_tbl_name=["submission"],
            table=pl.DataFrame({"submission_status": [status]}),
            filter_coln_var=["submission_name", "organism", "database", "submission_type"],
            filter_coln_val={
                "submission_name": [submission_name],
                "organism": [organism],
                "database": [target_database],
                "submission_type": [target_submission_type],
            },
            filter_var_by=["AND", "AND", "AND"],
        )


def _read_seqsender_error(log_path: str, max_bytes: int = 16_384) -> str:
    try:
        with open(log_path, "rb") as log_file:
            log_file.seek(0, os.SEEK_END)
            log_size = log_file.tell()
            log_file.seek(max(0, log_size - max_bytes))
            return log_file.read().decode("utf-8", errors="replace").strip()
    except OSError as err:
        logger.warning("Unable to read SeqSender log '%s': %s", log_path, err)
        return ""


# Function to update the submitter information in the database with the provided submitter information
def update_submitter_in_database(
    submitter_name: str,
    submission_portal: str,
    submitter_tbl: pl.DataFrame,
    return_tbl: bool = False
) -> Optional[pl.DataFrame]:
    """
    Update submitter in the database with the provided submitter information.
    
    Args:
        submitter_name (str): Name of the submitter.
        submission_portal (str): Submission portal used by the submitter.
        submitter_tbl (pl.DataFrame): Submitter table containing submitter information.
        return_tbl (bool, optional): Whether to return the updated submitter table. Defaults to False.

    Returns:
        Optional[pl.DataFrame]: Updated submitter table if return_tbl is True, otherwise None.
    """
    try:
        # Check if submitter for this submitter_name exists in database
        db_submitter_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submitter"],
            return_var = ["*"],
            filter_coln_var = ["submitter_name", "submission_portal"],
            filter_coln_val = {"submitter_name": [submitter_name], "submission_portal": [submission_portal]},
            filter_var_by = ["AND", "AND"]
        )
        # Make sure db table match the schema data types
        db_submitter_tbl = db_submitter_tbl.with_columns([
            _cast_expr(col, submitter_db_schema.columns[col].dtype.type) for col in submitter_db_schema.columns
        ])
        # Validate db table against the schema
        db_submitter_tbl = validate_tbl(db_submitter_tbl, submitter_db_schema, "submitter")
        # Make sure submission table match the schema data types
        submitter_tbl = submitter_tbl.with_columns([
            _cast_expr(col, submitter_pa_schema.columns[col].dtype.type) for col in submitter_pa_schema.columns
        ])
        # Validate submission table against the schema
        submitter_tbl = validate_tbl(submitter_tbl, submitter_pa_schema, "submitter")
        # Check if db_submitter_tbl is empty, if so insert new submitter_tbl to database
        if db_submitter_tbl.is_empty():
            insert_tbl_to_database(
                db_tbl_name = ["submitter"],
                table = submitter_tbl
            )
        else:
            # Compare and update database table
            compare_and_update_db_table(
                unique_cols = ["submitter_name", "submission_portal"],
                compare_tbl = submitter_tbl,
                db_tbl = db_submitter_tbl,
                db_tbl_name = "submitter"
            )
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    # Whether to return database table
    if return_tbl:
        db_submitter_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submitter"],
            return_var = ["*"],
            filter_coln_var = ["submitter_name", "submission_portal"],
            filter_coln_val = {"submitter_name": [submitter_name], "submission_portal": [submission_portal]},
            filter_var_by = ["AND", "AND"]
        )
        return db_submitter_tbl
    else:
        return None

# Function to update the submission worksheet in the database with the provided submission information
def update_submission_in_database(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
    submission_tbl: pl.DataFrame,
    return_tbl: bool = False
) -> Optional[pl.DataFrame]:
    """
    Update the submission worksheet in the database with the provided submission information.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.
        submission_tbl (pl.DataFrame): Submission table containing submission information.
        return_tbl (bool, optional): Whether to return the updated submission table. Defaults to False.

    Returns:
        Optional[pl.DataFrame]: Updated submission table if return_tbl is True, otherwise None.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        
        # Make sure db table match the schema data types
        db_submission_tbl = db_submission_tbl.with_columns([
            _cast_expr(col, submission_db_schema.columns[col].dtype.type) for col in submission_db_schema.columns
        ])
        # Validate db table against the schema
        db_submission_tbl = validate_tbl(db_submission_tbl, submission_db_schema, "submission")
        # Make sure submission table match the schema data types
        submission_tbl = submission_tbl.with_columns([
            _cast_expr(col, submission_pa_schema.columns[col].dtype.type) for col in submission_pa_schema.columns
        ])
        # Validate submission table against the schema
        submission_tbl = validate_tbl(submission_tbl, submission_pa_schema, "submission")
        # Check if db_submission_tbl is empty, if so insert new submission_tbl to database
        if db_submission_tbl.is_empty():
            insert_tbl_to_database(
                db_tbl_name = ["submission"],
                table = submission_tbl
            )
        else:
            # Compare and update database table
            compare_and_update_db_table(
                unique_cols = ["submission_name", "organism", "database", "submission_type"],
                compare_tbl = submission_tbl,
                db_tbl = db_submission_tbl,
                db_tbl_name = "submission"
            )    
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    # Whether to return database table
    if return_tbl:
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        return db_submission_tbl
    else:
        return None
    

# Retrieve submission information from the database for a given submission name, organism, database, and submission type
def retrieve_submission(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission information from the database for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        Dict[str, Any]: Dictionary containing the status, message, and submission information.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.is_empty():
            return {
                "submission_info": None,
                "message": f"Submission '{submission_name}' does not exist in the database.",
            }
        else:
            return {
                "submission_info": db_submission_tbl.to_dicts(),
                "message": f"Submission '{submission_name}' has been successfully retrieved.",
            }
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))


# Render the SeqSender config.yaml template with the submitter's credentials pulled from the
# database (per the submitter schema), and write it into the submission's directory.
def create_seqsender_config_file(
    ncbi_submitter_name: Optional[str],
    gisaid_submitter_name: Optional[str],
    submission_name: str,
    organism: str,
    database: List[str],
) -> None:
    try:
        # NCBI section is needed if any non-GISAID database is active; GISAID section only if GISAID is active
        needs_ncbi = any(db != "GISAID" for db in database)
        needs_gisaid = "GISAID" in database

        # Read in the config template file
        with open(CONFIG_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        # Populate the config with the submitter's credentials from the database
        if needs_ncbi:
            submission_tbl = lookup_tbl_in_database(
                db_tbl_name = ["submission"],
                return_var = ["*"],
                filter_coln_var = ["submission_name", "submission_portal"],
                filter_coln_val = {"submission_name": [submission_name], "submission_portal": ["NCBI"]},
                filter_var_by = ["AND", "AND"]
            )
            ncbi_tbl = lookup_tbl_in_database(
                db_tbl_name = ["submitter"],
                return_var = ["*"],
                filter_coln_var = ["submitter_name", "submission_portal"],
                filter_coln_val = {"submitter_name": [ncbi_submitter_name], "submission_portal": ["NCBI"]},
                filter_var_by = ["AND", "AND"]
            )
            if submission_tbl.is_empty():
                raise ValueError(f"NCBI submission '{submission_name}' does not exist in the database.")
            if ncbi_tbl.is_empty():
                raise ValueError(f"NCBI submitter '{ncbi_submitter_name}' does not exist in the database.")
            # Convert null to empty string
            submission_tbl = submission_tbl.with_columns(
                pl.col(pl.String).fill_null("")
            )
            ncbi_tbl = ncbi_tbl.with_columns(
                pl.col(pl.String).fill_null("")
            )
            # Extract the first row from the NCBI table as a dictionary
            ncbi_row = ncbi_tbl.to_dicts()[0]
            submission_row = submission_tbl.to_dicts()[0]
            text = lambda value: "" if value is None else str(value)
            postal_code = text(ncbi_row["ncbi_addr_postal_code"]).strip()
            if not postal_code.isdigit():
                raise ValueError("NCBI postal code must contain only digits for SeqSender.")
            ncbi_cfg = config["Submission"]["NCBI"]
            ncbi_cfg["Username"] = text(ncbi_submitter_name)
            ncbi_cfg["Password"] = text(ncbi_row["submitter_password"])
            ncbi_cfg["Spuid_Namespace"] = text(ncbi_row["ncbi_spuid_namespace"])
            ncbi_cfg["BioSample_Package"] = text(biosample_packages[organism])
            ncbi_cfg["Publication_Title"] = text(submission_row["ncbi_publication_title"])
            publication_status = text(submission_row["ncbi_publication_status"])
            ncbi_cfg["Publication_Status"] = text(publication_status)
            ncbi_cfg["Specified_Release_Date"] = text(submission_row["ncbi_release_date"])
            org = ncbi_cfg["Description"]["Organization"]
            org["Role"] = text(ncbi_row["ncbi_org_role"])
            org["Type"] = text(ncbi_row["ncbi_org_type"])
            org["Name"] = text(ncbi_row["ncbi_org_name"])
            addr = org["Address"]
            addr["Affil"] = text(ncbi_row["ncbi_org_affiliation"])
            addr["Div"] = text(ncbi_row["ncbi_org_division"])
            addr["Street"] = text(ncbi_row["ncbi_addr_street"])
            addr["City"] = text(ncbi_row["ncbi_addr_city"])
            addr["Sub"] = text(ncbi_row["ncbi_addr_state"])
            addr["Postal_Code"] = int(postal_code)
            addr["Country"] = text(ncbi_row["ncbi_addr_country"])
            addr["Email"] = text(ncbi_row["ncbi_addr_email"])
            addr["Phone"] = text(ncbi_row["ncbi_addr_phone"])
            submitter_cfg = org["Submitter"]
            submitter_cfg["Email"] = text(ncbi_row["ncbi_submitter_email"])
            submitter_cfg["Alt_Email"] = text(ncbi_row["ncbi_submitter_alt_email"])
            submitter_cfg["Name"]["First"] = text(ncbi_row["ncbi_submitter_first_name"])
            submitter_cfg["Name"]["Last"] = text(ncbi_row["ncbi_submitter_last_name"])
        else:
            del config["Submission"]["NCBI"]

        # Populate the GISAID section of the config if needed
        if needs_gisaid:
            gisaid_tbl = lookup_tbl_in_database(
                db_tbl_name = ["submitter"],
                return_var = ["*"],
                filter_coln_var = ["submitter_name", "submission_portal"],
                filter_coln_val = {"submitter_name": [gisaid_submitter_name], "submission_portal": ["GISAID"]},
                filter_var_by = ["AND", "AND"]
            )
            if gisaid_tbl.is_empty():
                raise ValueError(f"GISAID submitter '{gisaid_submitter_name}' does not exist in the database.")
            gisaid_row = gisaid_tbl.to_dicts()[0]
            gisaid_cfg = config["Submission"]["GISAID"]
            gisaid_cfg["Client-Id"] = text(gisaid_row["gisaid_client_id"])
            gisaid_cfg["Username"] = text(gisaid_submitter_name)
            gisaid_cfg["Password"] = text(gisaid_row["submitter_password"])
        else:
            del config["Submission"]["GISAID"]

        # Write the rendered config into the submission's directory
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        os.makedirs(submission_name_dir, exist_ok=True)
        config_file_path = os.path.join(submission_name_dir, CONFIG_FILENAME)
        with open(config_file_path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, sort_keys=False)
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    
    
# Create a SeqSender submission for a given submission name, organism, database, and submission type
def create_seqsender_submission(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
    ncbi_submitter_info: Optional[pl.DataFrame] = None,
    gisaid_submitter_info: Optional[pl.DataFrame] = None,
    gff_file: Optional[bool] = False,
    table2asn: Optional[bool] = False,
    ncbi_publication_title: Optional[str] = None,
    ncbi_publication_status: str = "Unpublished",
    ncbi_release_date: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        # Create NCBI submitter
        ncbi_submitter_tbl = ncbi_submitter_info
        if ncbi_submitter_tbl is not None and not ncbi_submitter_tbl.is_empty():
            row = ncbi_submitter_tbl.to_dicts()[0]
            submitter_name = row["submitter_name"]
            submission_portal = "NCBI"
            ncbi_submitter_name = row["submitter_name"]
            update_submitter_in_database(
                submitter_name = submitter_name,
                submission_portal = submission_portal,
                submitter_tbl = ncbi_submitter_tbl,
                return_tbl = True
            )
        else:
            ncbi_submitter_name = None

        # Create GISAID submitter
        gisaid_submitter_tbl = gisaid_submitter_info
        if gisaid_submitter_tbl is not None and not gisaid_submitter_tbl.is_empty():
            row = gisaid_submitter_tbl.to_dicts()[0]
            submitter_name = row["submitter_name"]
            submission_portal = "GISAID"
            gisaid_submitter_name = row["submitter_name"]
            update_submitter_in_database(
                submitter_name = submitter_name,
                submission_portal = submission_portal,
                submitter_tbl = gisaid_submitter_tbl,
                return_tbl = True
            )
        else:
            gisaid_submitter_name = None

        # Create submission table
        submission_tbl = pl.DataFrame({
            "submission_name": [submission_name for db in database],
            "organism": [organism for db in database],
            "submission_portal": ["NCBI" if db != "GISAID" else "GISAID" for db in database],
            "database": [db for db in database],
            "database_status": ["ACTIVE" for db in database],
            "submission_type": [submission_type if db != "GISAID" else "PRODUCTION" for db in database],
            "gff_file": [gff_file if db != "GISAID" else False for db in database],
            "table2asn": [table2asn if db != "GISAID" else False for db in database],
            "submitter_name": [ncbi_submitter_name if db != "GISAID" else gisaid_submitter_name for db in database],
            "ncbi_publication_title": [ncbi_publication_title if db != "GISAID" else None for db in database],
            "ncbi_publication_status": [ncbi_publication_status if db != "GISAID" else "Unpublished" for db in database],
            "ncbi_release_date": [ncbi_release_date if db != "GISAID" else None for db in database],
            "submission_status": ["CREATED" for db in database],
        })

        # Update submission worksheet in database
        db_submission_tbl = update_submission_in_database(
            submission_name = submission_name,
            organism = organism,
            database = database,
            submission_type = submission_type,
            submission_tbl = submission_tbl,
            return_tbl = True
        )

        # Create config file after the submission rows exist so NCBI publication and release
        # values can be read from the submission table.
        create_seqsender_config_file(
            ncbi_submitter_name = ncbi_submitter_name,
            gisaid_submitter_name = gisaid_submitter_name,
            submission_name = submission_name,
            organism = organism,
            database = database,
        )

        # Return
        return {
            "status":  "success",
            "message": f"Submission '{submission_name}' has been successfully created.",
            "submission_info": db_submission_tbl.to_dicts(),
        }
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    

# Retrieve submission config file for a given submission name, organism, database, and submission type
def retrieve_seqsender_config(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission config for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission config file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve config file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        config_file_path = os.path.join(submission_name_dir, CONFIG_FILENAME)
        if not os.path.exists(config_file_path):
            raise ValueError(f"Config file '{CONFIG_FILENAME}' does not exist in submission directory '{submission_name_dir}'.")
        # Return file path
        return config_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    

# Retrieve submission metadata for a given submission name, organism, database, and submission type
def retrieve_seqsender_metadata(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission metadata for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission metadata file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        metadata_file_path = os.path.join(submission_name_dir, METADATA_FILENAME)
        if not os.path.exists(metadata_file_path):
            raise ValueError(f"Metadata file '{METADATA_FILENAME}' does not exist in submission directory '{submission_name_dir}'.")
        # Return file path
        return metadata_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))

    
# Retrieve submission fasta file for a given submission name, organism, database, and submission type
def retrieve_seqsender_fasta(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission fasta file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission fasta file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        fasta_file_path = os.path.join(submission_name_dir, FASTA_FILENAME)
        if not os.path.exists(fasta_file_path):
            raise ValueError(f"Fasta file '{FASTA_FILENAME}' does not exist in submission directory '{submission_name_dir}'.")
        # Return file path
        return fasta_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))   


# Retrieve raw read files for a given submission name, organism, database, and submission type
def retrieve_seqsender_raw_reads(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> List[str]:
    """Return the paths of raw read files stored for an existing submission."""
    try:
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
            raise ValueError(f"Submission '{submission_name}' does not exist in the database.")

        raw_reads_dir = os.path.realpath(os.path.join(
            _DEFAULT_SEQSENDER_STORAGE_PATH,
            organism,
            submission_name,
            "raw_reads"
        ))
        if not os.path.isdir(raw_reads_dir):
            raise ValueError(f"Raw reads do not exist for submission '{submission_name}'.")

        raw_read_paths = sorted(
            os.path.join(raw_reads_dir, filename)
            for filename in os.listdir(raw_reads_dir)
            if os.path.isfile(os.path.join(raw_reads_dir, filename))
        )
        if not raw_read_paths:
            raise ValueError(f"Raw reads do not exist for submission '{submission_name}'.")
        return raw_read_paths
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))


def validate_seqsender_uploaded_files(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
    require_gff: bool = False,
) -> Dict[str, Any]:
    
    """Report whether files required to resubmit an existing submission are stored."""
    db_submission_tbl = lookup_tbl_in_database(
        db_tbl_name = ["submission"],
        return_var = ["*"],
        filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
        filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
        filter_var_by = ["AND", "AND", "AND", "AND"]
    )
    if db_submission_tbl.shape[0] == 0:
        raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
    # Ensure that the submission exists in the database before proceeding.
    selected_databases = db_submission_tbl.select("database").unique().to_series().to_list()
    submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
    submission_name_dir = os.path.join(submission_dir, submission_name)
    raw_reads_dir = os.path.join(submission_name_dir, "raw_reads")
    gisaid_cli_dir = os.path.join(submission_dir, "gisaid_cli")
    file_status = {
        "metadata": os.path.isfile(os.path.join(submission_name_dir, METADATA_FILENAME)),
        "fasta": os.path.isfile(os.path.join(submission_name_dir, FASTA_FILENAME)),
        "raw_reads": "SRA" not in selected_databases or (
            os.path.isdir(raw_reads_dir)
            and any(
                os.path.isfile(os.path.join(raw_reads_dir, filename))
                for filename in os.listdir(raw_reads_dir)
            )
        ),
        "gisaid_cli": "GISAID" not in selected_databases or os.path.isfile(os.path.join(
            gisaid_cli_dir,
            organism.lower() + "CLI",
        )),
        "gff": not require_gff or os.path.isfile(os.path.join(submission_name_dir, GFF_FILENAME)),
    }
    labels = {
        "metadata": "Metadata File",
        "fasta": "FASTA File",
        "raw_reads": "Raw Reads (FASTQs)",
        "gisaid_cli": "GISAID CLI",
        "gff": "GFF File",
    }
    return {
        "files": file_status,
        "missing_files": [
            {"key": key, "label": labels[key]}
            for key, exists in file_status.items()
            if not exists
        ],
    }


# Retrieve gff file for a given submission name, organism, database, and submission type
def retrieve_seqsender_gff(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission gff file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission gff file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        gff_file_path = os.path.join(submission_name_dir, GFF_FILENAME)
        if not os.path.exists(gff_file_path):
            raise ValueError(f"GFF file '{GFF_FILENAME}' does not exist in submission directory '{submission_name_dir}'.")
        # Return file path
        return gff_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))   


# Retrieve table2asn file for a given submission name, organism, database, and submission type
def retrieve_seqsender_table2asn(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission table2asn file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission table2asn file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        table2asn_file_path = os.path.join(submission_name_dir, TABLE2ASN_FILENAME)
        if not os.path.exists(table2asn_file_path):
            raise ValueError(f"Table2asn file '{TABLE2ASN_FILENAME}' does not exist in submission directory '{submission_name_dir}'.")
        # Return file path
        return table2asn_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))   
    

# Retrieve gisaid cli file for a given submission name, organism, database, and submission type
def retrieve_seqsender_gisaid_cli(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission GISAID CLI file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        Dict[str, Any]: Dictionary containing the details of the submission GISAID CLI file location.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        GISAID_CLI_FILENAME = organism.lower() + "CLI"
        gisaid_cli_file_path = os.path.join(submission_dir, GISAID_CLI_FILENAME)
        if not os.path.exists(gisaid_cli_file_path):
            raise ValueError(f"GISAID CLI file '{GISAID_CLI_FILENAME}' does not exist in submission directory '{submission_dir}'.")
        # Return file path
        return {"gisaid_cli_file_path": gisaid_cli_file_path}
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))

    
# Retrieve submission log file for a given submission name, organism, database, and submission type
def retrieve_seqsender_submission_log(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission log file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        str: Path to the submission log file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        submission_log_file_path = os.path.join(submission_name_dir, SUBMISSION_LOG_FILENAME)
        if not os.path.exists(submission_log_file_path):
            return None
        else:
            return submission_log_file_path
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    

# Retrieve submission status report file for a given submission name, organism, database, and submission type
def retrieve_seqsender_status_report(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Retrieve submission status report file for a given submission name, organism, database, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        Dict[str, Any]: Dictionary containing the path to the submission status report file.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Retrieve metadata file path
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH))
        submission_name_dir = os.path.join(submission_dir, submission_name)
        submission_status_report_file_path = os.path.join(submission_name_dir, SUBMISSION_STATUS_REPORT_FILENAME)
        if not os.path.exists(submission_status_report_file_path):
            return {"submission_status_report_file_path": None}
        else:
            return {"submission_status_report_file_path": submission_status_report_file_path}
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))
    

# Function to submit submission to the specified database for a given submission name, organism, and submission type
def submit_seqsender_submission(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str
) -> Dict[str, Any]:
    """
    Submit submission to the specified database for a given submission name, organism, and submission type.
    
    Args:
        submission_name (str): Name of the submission.
        organism (str): Type of organism.
        database (List[str]): List of databases to submit to.
        submission_type (str): Type of submissions: Test or Production.

    Returns:
        Dict[str, Any]: Dictionary containing the status and message of the submission process.
    """
    try:
        # Check if submission for this submission_name exists in database
        db_submission_tbl = lookup_tbl_in_database(
            db_tbl_name = ["submission"],
            return_var = ["*"],
            filter_coln_var = ["submission_name", "organism", "database", "submission_type"],
            filter_coln_val = {"submission_name": [submission_name], "organism": [organism], "database": database, "submission_type": [submission_type]},
            filter_var_by = ["AND", "AND", "AND", "AND"]
        )
        # Check if submission exists in the database
        if db_submission_tbl.shape[0] == 0:
           raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
        # Define the submission directory as seen by this backend process (used for local
        # file-existence checks, Popen's cwd, and the stdout log file).
        submission_dir = os.path.realpath(os.path.join(_DEFAULT_SEQSENDER_STORAGE_PATH, organism))
        submission_name_dir = os.path.join(submission_dir, submission_name)

        # Run the copied SeqSender application in its isolated Micromamba environment.
        seqsender_dir = os.environ.get("SEQSENDER_DIR", "/seqsender")
        seqsender_script = os.path.join(seqsender_dir, "seqsender.py")
        mamba_root_prefix = os.environ.get("MAMBA_ROOT_PREFIX", "/opt/conda")
        seqsender_python = os.path.join(mamba_root_prefix, "envs", "seqsender", "bin", "python")
        if not os.path.isfile(seqsender_python):
            raise FileNotFoundError(f"SeqSender Python interpreter '{seqsender_python}' does not exist.")
        if not os.path.isfile(seqsender_script):
            raise FileNotFoundError(f"SeqSender executable '{seqsender_script}' does not exist.")
        prep_cmd = [
            seqsender_python,
            seqsender_script,
            "prep",
        ]
        cmd = [
            "--submission_dir", submission_dir,
            "--submission_name", submission_name,
            "--organism", organism
        ]
        # Check if config file exists in the submission directory
        config_file = os.path.join(submission_name_dir, CONFIG_FILENAME)
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file '{config_file}' does not exist.")
        else:
            cmd.extend(["--config_file", config_file])
        # Check if metadata file exists in the submission directory
        metadata_file = os.path.join(submission_name_dir, METADATA_FILENAME)
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file '{metadata_file}' does not exist.")
        else:
            cmd.extend(["--metadata_file", metadata_file])
        # Check if fasta file exists in the submission directory
        fasta_file = os.path.join(submission_name_dir, FASTA_FILENAME)
        if not os.path.exists(fasta_file):
            raise FileNotFoundError(f"FASTA file '{fasta_file}' does not exist.")
        else:
            cmd.extend(["--fasta_file", fasta_file])
        # If gff file is true, check if it exists
        gff_file = db_submission_tbl.select("gff_file").to_series().to_list()[0]
        if gff_file:
            gff_file_path = os.path.join(submission_name_dir, GFF_FILENAME)
            if not os.path.exists(gff_file_path):
                raise FileNotFoundError(f"GFF file '{gff_file_path}' does not exist.")
            cmd.extend(["--gff_file", gff_file_path])
        # If table2asn is true, check if it exists
        table2asn = db_submission_tbl.select("table2asn").to_series().to_list()[0]
        if table2asn:
            cmd.extend(["--table2asn"])
        # If GISAID is in the database list, add the GISAID CLI to the command
        if "GISAID" in [db.strip().upper() for db in database]:
            gisaid_cli_file_path = os.path.join(submission_dir, "gisaid_cli", organism.lower() + "CLI")
            if not os.path.exists(gisaid_cli_file_path):
                raise FileNotFoundError(f"GISAID CLI file '{gisaid_cli_file_path}' does not exist.")
            cmd.extend(["--gisaid"])
        # Check if BioSample is in the database list
        if "BIOSAMPLE" in [db.strip().upper() for db in database]:
            cmd.extend(["--biosample"])
        # Check if SRA is in the database list
        if "SRA" in [db.strip().upper() for db in database]:
            cmd.extend(["--sra"])
        # Check if GenBank is in the database list
        if "GENBANK" in [db.strip().upper() for db in database]:
            cmd.extend(["--genbank"])

        # Log the command that will be executed
        logger.info(
            f"Launching SeqSender pipeline for submission '{submission_name}' with command:\n" +
            f"{seqsender_python} {seqsender_script} prep\n" +
            f" --submission_dir {submission_dir}\n" +
            f" --submission_name {submission_name}\n" +
            f" --organism {organism}\n" +
            f" --config_file {config_file}\n" +
            f" --metadata_file {metadata_file}\n" +
            f" --fasta_file {fasta_file}\n" +
            (f" --gff_file {gff_file_path}\n" if gff_file else "") +
            (f" --table2asn\n" if table2asn else "") +
            (f" --gisaid\n" if "GISAID" in [db.strip().upper() for db in database] else "") +
            (f" --biosample\n" if "BIOSAMPLE" in [db.strip().upper() for db in database] else "") +
            (f" --sra\n" if "SRA" in [db.strip().upper() for db in database] else "") +
            (f" --genbank\n" if "GENBANK" in [db.strip().upper() for db in database] else "")
        )    

        # Create seqsender_stdout.log file in the submission directory
        seqsender_stdout_path = os.path.join(submission_name_dir, "seqsender.stdout.log")
        stdout_fh = open(seqsender_stdout_path, "w", encoding="utf-8")

        # Run SeqSender asynchronously so the API can return its PID immediately.
        submit_proc = subprocess.Popen(
            prep_cmd + cmd,
            cwd=submission_name_dir,
            stdout=stdout_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        # The child has inherited its own copy of the file descriptor; the parent's copy
        # is no longer needed and can be closed safely.
        stdout_fh.close()

        # Record the process information in the global dictionary with thread safety.
        with _SEQSENDER_PROCESS_LOCK:
            _SEQSENDER_PROCESSES[submit_proc.pid] = {
                "process": submit_proc,
                "identity": _seqsender_process_identity(
                    submission_name,
                    organism,
                    database,
                    submission_type,
                ),
                "log_path": seqsender_stdout_path,
            }

        # Return the process ID and command for reference
        return {
            "status":  "success",
            "pid":     submit_proc.pid,
        }
    except ValueError as err:
        raise ValueError(str(err))
    except Exception as err:
        raise Exception(str(err))

# Check the lifecycle status of a SeqSender child process without a background waiter.
def retrieve_seqsender_process_status(
    submission_name: str,
    organism: str,
    database: List[str],
    submission_type: str,
    pid: int,
) -> Dict[str, Any]:
    # Ensure the submission exists in the database before attempting to retrieve its status.
    db_submission_tbl = lookup_tbl_in_database(
        db_tbl_name=["submission"],
        return_var=["*"],
        filter_coln_var=["submission_name", "organism", "database", "submission_type"],
        filter_coln_val={
            "submission_name": [submission_name],
            "organism": [organism],
            "database": database,
            "submission_type": [submission_type],
        },
        filter_var_by=["AND", "AND", "AND", "AND"],
    )
    if db_submission_tbl.shape[0] == 0:
        raise ValueError(f"Submission '{submission_name}' does not exist in the database.")
    identity = _seqsender_process_identity(submission_name, organism, database, submission_type)
    with _SEQSENDER_PROCESS_LOCK:
        terminal_result = _SEQSENDER_TERMINAL_RESULTS.get(pid)
        process_record = _SEQSENDER_PROCESSES.get(pid)

    if terminal_result is not None:
        if terminal_result["identity"] != identity:
            raise ValueError(f"SeqSender process status does not match PID {pid}.")
        return terminal_result["payload"]

    if process_record is None:
        raise FileNotFoundError(
            f"SeqSender PID {pid} is not tracked by this backend process. "
            "The backend may have restarted after the submission was launched."
        )
    if process_record["identity"] != identity:
        raise ValueError(f"SeqSender process status does not match PID {pid}.")

    process = process_record["process"]
    return_code = process.poll()
    if return_code is None:
        _update_seqsender_submission_status(
            submission_name,
            organism,
            database,
            submission_type,
            "PROCESSING",
        )
        return {
            "status": "PROCESSING",
            "pid": pid,
            "return_code": None,
            "message": "SeqSender submissions are being processed.",
        }

    if return_code == 0:
        status = "SUBMITTED"
        message = (
            "SeqSender submissions has been submitted successfully. "
            "User can track the SUBMISSION STATUS IN THE NEXT PANEL"
        )
    else:
        status = "FAILED"
        log_error = _read_seqsender_error(process_record["log_path"])
        message = f"SeqSender submissions failed with exit code {return_code}."
        if log_error:
            message = f"{message}\n{log_error}"

    _update_seqsender_submission_status(
        submission_name,
        organism,
        database,
        submission_type,
        status,
    )
    payload = {
        "status": status,
        "pid": pid,
        "return_code": return_code,
        "message": message,
    }
    with _SEQSENDER_PROCESS_LOCK:
        _SEQSENDER_PROCESSES.pop(pid, None)
        _SEQSENDER_TERMINAL_RESULTS[pid] = {"identity": identity, "payload": payload}
        while len(_SEQSENDER_TERMINAL_RESULTS) > _MAX_TERMINAL_RESULTS:
            oldest_pid = next(iter(_SEQSENDER_TERMINAL_RESULTS))
            _SEQSENDER_TERMINAL_RESULTS.pop(oldest_pid)
    return payload

# Function to extract metadata worksheet

        