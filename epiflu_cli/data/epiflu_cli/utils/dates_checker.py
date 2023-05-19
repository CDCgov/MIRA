"""
    Copyright (C) 2023 Friends of GISAID.
"""


from datetime import datetime, date
def formatdate(input_date, dateformat):
    """
    formatdate is used to coerce dates into a consistent format

    Given the variety of countries submitting to the platform, dates might 
    take a number of formats. This function aims to coerce an input_date in any
    format to (e.g., MM/DD/YYYY or DD.MM.YYYY) to YYYY-MM-DD. 

    Args:
        input_date (str): date from metadata file (may contain delimiters)
        dateformat (str): args.dateformat is a rule for the input_date format

    Returns:
        str: output date formatted in YYYY-MM-DD
    """
    input_date = input_date.strip(). \
                            replace("/", "-"). \
                            replace(".", "-"). \
                            replace("–", "-")
    datetrans = {"YYYYMMDD": "%Y-%m-%d",
                 "YYYYDDMM": "%Y-%d-%m",
                 "DDMMYYYY": "%d-%m-%Y",
                 "MMDDYYYY": "%m-%d-%Y"}
    input_date = datetime.strptime(input_date, datetrans[dateformat]).date()
    month = input_date.month
    day   = input_date.day
    year  = input_date.year
    return str(date(year, month, day))
