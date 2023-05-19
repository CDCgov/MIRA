#!/usr/bin/env python3

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

banner = html.Section(
    [
        html.H3("MIRA"),
        html.P("User-Friendly, Influenza Genome and SARS-CoV-2 Spike-Gene Assembly and Curation"),
        #html.Img(src="/assets/mermaid_flow.png", className="mira-flowchart-img", title="MIRA Flowchart", alt="MIRA FLowchart"),
    ],
    className="banner w-100 ps-5"
)

overview = html.Section(
    [
        html.Div(
            [
                html.Div(
                    html.Img(src="https://github.com/CDCgov/MIRA/raw/prod/man/figures/mira_flowchart_mermaid.png", width="100%", title="MIRA Flowchart", alt="MIRA FLowchart"),
                    className="overview-cell",
                ),
                html.Div(
                    [
                        html.Div(
                            "MIRA Overview",
                            className="title"
                        ),
                        html.Div(
                            "MIRA is an interactive dashboard created using Dash, a python framework written on the top of Flask, Plotly.js and React.js. The dashboard allows users to interactively create a metadata and config file for running Influenza Genome and SARS-CoV-2 Spike-Gene Assembly. Coming soon, it will allow for upload via FTP to NCBI’s databases Genbank, BioSample, and SRA, as well as GISAID.",
                            className="content"
                        )
                    ],
                    className="overview-cell border border-2 border-info rounded-3",
                )
            ],
            className="overview-table"
        )
    ],
    className="overview"
)

features = html.Section(
    [
        html.H3("Four Key Features of MIRA", className="text-center"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                                "IRMA",
                                className="title"
                            ),
                            html.Div(
                                "A genome assembly tool that is designed for the robust assembly, variant calling, and phasing of highly variable RNA viruses. IRMA is deployed with modules for influenza, ebolavirus and coronavirus.",
                                className="content"
                            )
                        ],
                    className="features-cell border border-2 border-info rounded-3"
                ),
                html.Div(
                    [
                        html.Div(
                            "DAIS-Ribosome",
                            className="title"
                        ),
                        html.Div(
                            "A curation tool that compartmentalizes the translation engine developed for the CDC Influenza Division protein analytics database. The tool has been extended for use with Betacoronavirus",
                            className="content"
                        )
                    ],
                    className="features-cell border border-2 border-info rounded-3",
                ),
                html.Div(
                    [
                        html.Div(
                            "Spyne",
                            className="title"
                        ),
                        html.Div(
                            "A Snakemake workflow manager designed for running Influenza Genome and SARS-CoV-2 Spike-Gene assembly.",
                            className="content"
                        )
                    ],
                    className="features-cell border border-2 border-info rounded-3",
                ),
                html.Div(
                    [
                        html.Div(
                            "MIRA",
                            className="title"
                        ),
                        html.Div(
                            "A GUI web interface that allows users to interactively create a metadata and config file for running Influenza Genome and SARS-CoV-2 Spike-Gene assembly and curation.",
                            className="content"
                        )
                    ],
                    className="features-cell border border-2 border-info rounded-3",
                )
            ],
            className="features-table d-flex flex-wrap align-items-top justify-content-between"
        )
    ],    
    className="features w-100 px-5"
)

layout = html.Div([banner, overview, features])

dash.register_page(
    __name__, 
    name="Upload",
    top_nav=True,
    order=3,
    layout=layout
)