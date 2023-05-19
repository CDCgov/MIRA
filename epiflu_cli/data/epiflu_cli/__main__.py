#!/usr/bin/env python3

"""
    Upload consensus sequences and metadata to GISAID's EpiFlu
    Copyright (C) 2023 Friends of GISAID.
"""

from datetime import datetime
import sys

STARTTIME = datetime.now()
TAB = "\t"
DATABASE = 'flu'


def get_execution_time():
    "Print total runtime at end of run."
    print(f"\nTotal runtime (HRS:MIN:SECS): {str(datetime.now() - STARTTIME)}")

def args_parser():
    """
    Argument parser setup and build.
    """
    import argparse, textwrap
    parser = argparse.ArgumentParser(prog = "epiflu_cli",
                                     formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                     description="Command Line Interface (CLI) for uploading Influenza sequence and metadata to GISAID's EpiFlu.")
    subparser_args1 = argparse.ArgumentParser(add_help=False)
    subparser_args2 = argparse.ArgumentParser(add_help=False)
    subparser_args3 = argparse.ArgumentParser(add_help=False)
    subparser_args4 = argparse.ArgumentParser(add_help=False)
    subparser_args5 = argparse.ArgumentParser(add_help=False)
    subparser_args6 = argparse.ArgumentParser(add_help=False)
    subparser_args7 = argparse.ArgumentParser(add_help=False)
    subparser_args8 = argparse.ArgumentParser(add_help=False)
    subparser_args9 = argparse.ArgumentParser(add_help=False)
    subparser_args2.add_argument("--token",
                                 help = "Authentication token.",
                                 default = 'flu.authtoken')
    subparser_args3.add_argument("--username",
                                 help = "Your GISAID username.",
                                 type = str)
    subparser_args3.add_argument("--password",
                                 help = "Your GISAID password.",
                                 type = str)
    subparser_args3.add_argument("--client_id",
                                 help = "Submitter's client-ID. Email clisupport[at]gisaid.org to request client-ID.")
    subparser_args3.add_argument("--force",
                                 help = "Switch on force overwrite of token given at --token",
                                 action = "store_true")
    subparser_args4.add_argument("--log",
                                 help = "All output logged here.",
                                 default = "./logfileFlu.log")
    subparser_args5.add_argument("--template",
                                 help = "Print submission 'template.csv' file per se.",
                                 action = "store_true")
    subparser_args6.add_argument("--metadata",
                                 help = "The csv-formatted metadata file.",
                                 required = True)
    subparser_args6.add_argument("--fasta",
                                 help = "The fasta-formatted nucleotide sequences file.",
                                 required = True)
    subparser_args7.add_argument("--proxy",
                                 help = "Proxy-configuration for HTTPS-Request in the form: 'proxyusername:proxypassword@proxy:port' or 'proxy:port' if no proxy authentication is required.",
                                 default=None)
    subparser_args8.add_argument("--debug",
                                 help = "Switch on traceback for debugging purposes.",
                                 default=False,
                                 action="store_true")
    subparser_args9.add_argument("--dateformat",
                                 help="Specify the date format, with 'Y' for 'year', 'M' for 'month', 'D' for 'day'. Dates will parse correctly with the following delimiters: '/', '.', '–' or '-'.",
                                 choices=["YYYYMMDD",
                                          "YYYYDDMM",
                                          "DDMMYYYY",
                                          "MMDDYYYY"],
                                 default="YYYYMMDD")


    subparser_modules = parser.add_subparsers(
        title="Sub-commands help", help="", metavar="", dest="subparser_name"
    )

    subparser_modules.add_parser(
        "authenticate",
        help="""Write the authentication token.""",
        description="Write the authentication token.",
        parents=[subparser_args1,
                 subparser_args2,
                 subparser_args3,
                 subparser_args4,
                 subparser_args7,
                 subparser_args8],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparser_modules.add_parser(
        "upload",
        help="""Upload sequences and metadata.""",
        description="Perform upload of sequences and metadata to GISAID's EpiFlu.",
        parents=[subparser_args1,
                 subparser_args2,
                 subparser_args4,
                 subparser_args6,
                 subparser_args7,
                 subparser_args8,
                 subparser_args9],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparser_modules.add_parser("labs",
        help = "Print laboratories with IDs available for uploading.",
        description = "Print laboratories with IDs available for uploading.",
        parents = [subparser_args2,
                   subparser_args4,
                   subparser_args7,
                   subparser_args8],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparser_modules.add_parser("version",
        help = "Show version and exit.")

    subparser_modules.add_parser("template",
        help = "Print template and formatting instructions",
        description="Print to stdout the formatting instructions for the metadata file, or print the 'template.csv' file per se.",
        parents = [subparser_args1,
                   subparser_args5,
                   subparser_args8],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    return parser


def main():
    """The main routine"""
    parser = args_parser()
    args = parser.parse_args()
    database = DATABASE
    if parser.parse_args().subparser_name is None:
        print("usage: epiflu_cli -h")
    elif args.subparser_name == "version":
        from epiflu_cli import __version__
        print(f"epiflu_cli version:{TAB}{__version__}")
    elif args.subparser_name == "template":
        from epiflu_cli.utils.instructions import INSTRUCTIONS
        from epiflu_cli.utils.colors import Colors
        if not args.template:
            for key, value in INSTRUCTIONS[database].items():
                print("")
                print(Colors.RED+key+':')
                print(Colors.BLUE+value+"\n")
        else:
            from epiflu_cli.utils.template import TEMPLATE
            print(TEMPLATE[database])
    else:
        from epiflu_cli.handler import handle
        try:
            exit_code = handle(args)
        except KeyboardInterrupt:
            print("user interrupt")
            sys.exit(1)
        get_execution_time()
        sys.exit(exit_code) 
if __name__ == "__main__":

    import doctest
    doctest.testmod()
    main()

