# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# List all package dependencies to render pages in app.py
import dash
from dash import Dash, dcc, dash_table
from dash import Input, Output, State, html, callback
from dash_bootstrap_components._components.Container import Container
import dash_bootstrap_components as dbc
import dash_daq as daq

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

import pandas as pd
from math import ceil 
from itertools import cycle
from sys import path, argv
from os.path import dirname, realpath, isdir, isfile
import os
import yaml
import json
from glob import glob
from numpy import arange
import subprocess

# Load all scripts files
path.append(dirname(realpath(__file__)) + "/scripts/")
#import irma2dash  # type: ignore
#import dais2dash  # type: ignore
import conditional_color_range_perCol  # type: ignore

# Read in the config and retrieve DEBUG 
with open(argv[1], "r") as y:
    CONFIG = yaml.safe_load(y)

DEBUG = CONFIG["DEBUG"]

# Use BOOTSTRAP themes and FONT AWESOME icons
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="MIRA",
    use_pages=True
)

app.config["suppress_callback_exceptions"] = True

# Create a Navbar pages
navbar = dbc.Navbar(
    [
        # Use row and col to control vertical alignment of logo / brand
        html.A(
            [
                html.Img(src="/assets/irma-spy.jpg", height="40px", width="40px", title="MIRA", alt="MIRA"),
                dbc.NavbarBrand(
                    "MIRA",
                    className="mira-brand-text ms-2 fw-bold"
                ),
            ],
            href="/",
            style={"textDecoration": "none"},
            className="mira-brand d-flex flex-wrap align-items-center justify-content-start",
        ),             
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavItem(
                        dbc.NavLink(
                            [
                                page["name"],
                            ],
                            href=page["path"],
                            active="exact",
                            className="mira-navlink"
                        )
                    )
                    for page in dash.page_registry.values()         
                ],
                pills=True, 
                fill=True,
                className="mira-nav w-100 d-flex flex-wrap align-items-center justify-content-end",
            ),
            id="navbar-collapse",
            is_open=False,
            navbar=True,
        )
    ], 
    color="primary",
    dark=True,
    className="mira-navbar px-5"
)

# Add callback for toggling the collapse on small screens
@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Content of the Navbar page based a specific page selected
body = dash.page_container

# Create a footer to list copyright and contract information
footer = html.Section(
    [
        html.Span(["Copyright ", html.I(className="fa-regular fa-copyright"), " 2023 CDC. All Right Reserved."], className="footer-cell"),
        html.Div(
            [
                html.A(html.I(className="fa-brands fa-twitter fa-xl ms-5"), href=""),
                html.A(html.I(className="fa-brands fa-facebook fa-xl ms-5"), href=""),
                html.A(html.I(className="fa-brands fa-github fa-xl ms-5"), href=""),
            ],
            className="d-flex flex-wrap align-items-center justify-content-end"
        )
    ],
    className="footer w-100 px-5 d-flex flex-wrap align-items-center justify-content-between"
)

# Create app layout with various components
app.layout = html.Div([navbar, body, footer])

####################################################
####################### MAIN #######################
####################################################
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=DEBUG)
