#!/usr/bin/env python3

"""
    Upload consensus sequences and metadata to GISAID
    Copyright (C) 2023 Friends of GISAID.
"""

from setuptools import setup, find_packages
import epiflu_cli

LONG_DESCRIPTION = open("README.md").read()

setup(

    name=epiflu_cli.__name__,
    version=epiflu_cli.__version__,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "epiflu_cli = epiflu_cli.__main__:main"
        ]
    },

    description=epiflu_cli.__description__,
    long_description=LONG_DESCRIPTION,
    classifiers=["Topic :: Scientific/Engineering :: Bio-Informatics",
                 "Topic :: Scientific/Engineering :: Medical Science Apps.",
                 "Intended Audience :: Science/Research/Public_Health"],
    keywords=["GISAID",
              "upload",
              "consensus",
              "metadata",
              "influenza",
              "virus",
              "flu"],
    author=epiflu_cli.__author__,
    author_email=epiflu_cli.__author_email__,
    license=epiflu_cli.__license__,
    package_data={"": ["*.fa*",
                       "*.csv"]}
)
