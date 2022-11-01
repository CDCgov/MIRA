# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from cProfile import run
from symbol import comp_for
import dash
from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
import dash_bio as dbio
from dash.dependencies import Input, Output, State
import dash_daq as daq
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pandas as pd
from math import ceil, log10, sqrt
from itertools import cycle
from sys import path, argv
from os.path import dirname, realpath, isdir, isfile
import os
import yaml
import json
from glob import glob
from numpy import arange
import base64
import io
import subprocess
from flask_caching import Cache
import time

path.append(dirname(realpath(__file__)) + "/scripts/")
import irma2dash  # type: ignore
import dais2dash  # type: ignore
import conditional_color_range_perCol  # type: ignore

with open(argv[1], "r") as y:
    CONFIG = yaml.safe_load(y)
data_root = CONFIG["DATA_ROOT"]
DEBUG = CONFIG["DEBUG"]

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
app.title = "IRMA SPY"
app.config["suppress_callback_exceptions"] = True

cache_timeout = 60 * 60 * 24 * 28
cache = Cache(
    app.server,
    config={"CACHE_TYPE": "filesystem", "CACHE_DIR": f"{data_root}/cache-directory"},
)
# cache.clear()


previousClick = 0


@app.callback(
    [Output("select_sample", "options"), Output("select_sample", "value")],
    [Input("coverage-heat", "clickData"), Input("select_run", "value")],
)
@cache.memoize(timeout=cache_timeout)
def select_sample(plotClick, run):
    if not run:
        raise
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["df4"], orient="split"
    )
    samples = df["Sample"].unique()
    samples.sort()
    print(samples)
    options = [{"label": i, "value": i} for i in samples]
    global previousClick
    if not plotClick:
        value = samples[0]
    elif plotClick == previousClick:
        sample = sample
    elif plotClick["points"][0]["x"] != "all":
        previousClick = plotClick
        value = plotClick["points"][0]["x"]
    return options, value


@app.callback(
    Output("single_sample_figs", "children"),
    [
        Input("select_run", "value"),
        Input("select_sample", "value"),
        Input("cov_linear_y", "value"),
    ],
)
@cache.memoize(timeout=cache_timeout)
def single_sample_fig(run, sample, cov_linear_y):
    if not run or not sample:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["read_df"], orient="split"
    )
    df = df[df["Sample"] == sample]
    sankeyfig = irma2dash.dash_reads_to_sankey(df)
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["df"], orient="split"
    )
    segments = json.loads(generate_df(f"{data_root}/{run}"))["segments"]
    segcolor = json.loads(generate_df(f"{data_root}/{run}"))["segcolor"]
    coveragefig = createSampleCoverageFig(sample, df, segments, segcolor, cov_linear_y)
    content = dbc.Row(
        [
            dbc.Col(dcc.Graph(figure=sankeyfig), width=4, align="start"),
            dbc.Col(dcc.Graph(figure=coveragefig), width=8, align="center"),
        ]
    )
    return content


@cache.memoize(timeout=cache_timeout)
def generate_df(run_path):
    if not run_path:
        raise dash.exceptions.PreventUpdate
    run_path = os.path.join(run_path, "IRMA")
    coverage_df = irma2dash.dash_irma_coverage_df(
        run_path
    )  # argv[2]) #loadData('./test.csv')
    read_df = irma2dash.dash_irma_reads_df(run_path)
    alleles_df = irma2dash.dash_irma_alleles_df(run_path)
    indels_df = irma2dash.dash_irma_indels_df(run_path)
    ref_lens = irma2dash.reference_lens(run_path)
    segments, segset, segcolor = returnSegData(coverage_df)
    df4 = pivot4heatmap(coverage_df)
    df4.to_csv(run_path + "/mean_coverages.tsv", sep="\t", index=False)
    if "Coverage_Depth" in df4.columns:
        cov_header = "Coverage_Depth"
    else:
        cov_header = "Coverage Depth"
    sliderMax = df4[cov_header].max()
    # allFig = createAllCoverageFig(df, ",".join(segments), segcolor)
    irma_read_fig = create_irma_read_fig(read_df)
    dais_vars = dais2dash.compute_dais_variants(results_path=run_path + "/dais_results")
    return json.dumps(
        {
            "df": coverage_df.to_json(orient="split"),
            "df4": df4.to_json(orient="split"),
            "read_df": read_df.to_json(orient="split"),
            "indels_df": indels_df.to_json(orient="split"),
            "alleles_df": alleles_df.to_json(orient="split"),
            "dais_vars": dais_vars.to_json(orient="split"),
            "ref_lens": ref_lens,
            "cov_header": cov_header,
            "sliderMax": sliderMax,
            "segments": ",".join(segments),
            "segset": ",".join(segset),
            "segcolor": segcolor,
            # "allFig": allFig.to_json(),
            "irma_reads_fig": irma_read_fig.to_json(),
        }
    )


@app.callback(
    Output("samplesheet", "children"),
    [Input("sample_number", "value"), Input("select_run", "value")],
)
def generate_samplesheet(sample_number, run):
    if not sample_number:
        raise dash.exceptions.PreventUpdate
    if isfile(f"{data_root}/{run}/samplesheet.csv"):
        data = pd.read_csv(f"{data_root}/{run}/samplesheet.csv").to_dict("records")
    else:
        str_num_list = "".join(sample_number).split(",")
        bc_numbers = []
        try:
            for i in str_num_list:
                i = i.strip()
                if "-" in i:
                    start, stop = map(int, i.split("-"))
                    bc_numbers.extend([n for n in range(start, stop + 1)])
                else:
                    bc_numbers.append(int(i))
            bc_numbers = list(set(bc_numbers))
            bc_numbers.sort()
        except Exception as E:
            table = html.Div(
                f"Please fix the formatting of your number entry. A comma-seperated list of numbers and number-ranges is required."
            )
            return table
        data = [
            dict(
                **{
                    "Barcode #": f"barcode{i:02}",
                    "Sample ID": "",
                    "Sample Type": "Test",
                    "Barcode Expansion Pack": "LSK-109",
                }
            )
            for i in bc_numbers
        ]
        # print(data, type(data))
    ss = dash_table.DataTable(
        id="samplesheet_table",
        columns=[
            {"id": "Barcode #", "name": "Barcode #"},
            {"id": "Sample ID", "name": "Sample ID"},
            {"id": "Sample Type", "name": "Sample Type", "presentation": "dropdown"},
            {
                "id": "Barcode Expansion Pack",
                "name": "Barcode Expansion Pack",
                "presentation": "dropdown",
            },
        ],
        data=data,
        editable=True,
        dropdown={
            "Sample Type": {
                "options": [
                    {"label": i, "value": i} for i in ["+ Control", "- Control", "Test"]
                ]
            },
            "Barcode Expansion Pack": {
                "options": [
                    {"label": i, "value": i}
                    for i in ["EXP-PBC096", "LSK-109", "SQK-NSK007", "SQK-PBK004"]
                ]
            },
        },
        export_format="csv",
        export_headers="display",
        merge_duplicate_headers=True,
        persistence=True,
    )
    table = ss
    return table


@cache.memoize(timeout=cache_timeout)
@app.callback(
    Output("output-container-button", "children"),
    [
        Input("assembly-button", "n_clicks"),
        Input("select_run", "value"),
        Input("experiment_type", "value"),
    ],
)
def run_snake_script_onClick(n_clicks, run, experiment_type):
    # print('[DEBUG] n_clicks:', n_clicks)
    if not n_clicks:
        # raise dash.exceptions.PreventUpdate
        return dash.no_update
    if not run:
        raise dash.exceptions.PreventUpdate
    if not experiment_type:
        raise dash.exceptions.PreventUpdate
    docker_cmd = "docker exec -w /data -it sc2-spike-seq-dev-1.0.3 bash snake-kickoff "
    docker_cmd += f"/data/{run}/samplesheet.csv "
    docker_cmd += f"/data/{run} "
    docker_cmd += experiment_type
    result = subprocess.check_output(docker_cmd, shell=True
    )
    # convert bytes to string
    result = result.decode()
    return result


def flfor(x, digits):
    return float(f"{x:.{digits}f}")


@app.callback([Output("minor_alleles_table", "children"), Input("select_run", "value")])
def alleles_table(run):
    if not run:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["alleles_df"], orient="split"
    )
    table = [
        html.Div(
            [
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict("records"),
                    sort_action="native",
                    filter_action="native",
                    # persistence=True,
                    page_size=10,
                    export_format="xlsx",
                    export_headers="display",
                    style_cell={"textAlign": "left", "height": "auto"},
                )
            ]
        )
    ]
    return table


@app.callback([Output("indels_table", "children"), Input("select_run", "value")])
def indels_table(run):
    if not run:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["indels_df"], orient="split"
    )
    table = [
        html.Div(
            [
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict("records"),
                    sort_action="native",
                    filter_action="native",
                    # persistence=True,
                    page_size=10,
                    export_format="xlsx",
                    export_headers="display",
                    style_cell={"textAlign": "left", "height": "auto"},
                )
            ]
        )
    ]
    return table


@app.callback([Output("vars_table", "children"), Input("select_run", "value")])
def vars_table(run):
    if not run:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["dais_vars"], orient="split"
    )
    table = [
        html.Div(
            [
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict("records"),
                    sort_action="native",
                    filter_action="native",
                    # persistence=True,
                    page_size=10,
                    export_format="xlsx",
                    export_headers="display",
                    style_cell={
                        "whiteSpace": "normal",
                        "textAlign": "left",
                        "height": 40,
                    },
                )
            ]
        )
    ]
    return table


def pandas_read_csv_progress(file, sep, usecols, engine="c", chunksize=100000):
    rc = sum(1 for row in open(file))
    # if usecols != "":
    df_iterator = pd.read_csv(
        file,
        usecols=usecols,
        sep=sep,
        engine=engine,
        iterator=True,
        chunksize=chunksize,
    )
    df = pd.DataFrame()
    chunk_count = chunksize
    for chunk in df_iterator:
        df = pd.concat([df, chunk])
        print(f"Reading {file} :: {(chunk_count/rc)*100:.0f}%")
        chunk_count += chunksize
    return df


@app.callback(
    [Output("illumina_demux_table", "children"), Output("demux_fig", "figure")],
    [Input("select_run", "value"),],
    prevent_initial_call=True,
)
@cache.memoize(timeout=cache_timeout)
def demux_table(run):
    # if not demux_file:
    # raise dash.exceptions.PreventUpdate
    glob_files = [
        f
        for f_ in [
            glob(n)
            for n in [
                f"{data_root}/{run}/sequencing_summary_*txt",
                f"{data_root}/{run}/laneBarcode.html",
            ]
        ]
        for f in f_
    ]
    print(f"start reading {glob_files[0]}")
    start = time.perf_counter()
    if len(glob_files) == 1:
        if "sequencing_summary" in glob_files[0]:
            df = pandas_read_csv_progress(
                glob_files[0],
                sep="\t",
                usecols=[
                    "alias",
                    "barcode_arrangement",
                    "filename_fastq",
                    "sequence_length_template",
                    "mean_qscore_template",
                    "barcode_score",
                ],
            )
        else:
            df = pd.read_html(glob_files[0])[2]
    ont = False
    print(f"reading in {glob_files[0]} took {time.perf_counter() - start} seconds.")
    if "filename_fastq" in df.columns:
        ont = True
        df = df.groupby(["alias", "barcode_arrangement"]).agg(
            {
                "filename_fastq": "count",
                "sequence_length_template": "mean",
                "mean_qscore_template": "mean",
                "barcode_score": "mean",
            }
        )
        df = df.reset_index()
        df = df.rename(
            columns={
                "barcode_arrangement": "Barcode",
                "alias": "Sample ID",
                "filename_fastq": "# Reads",
                "sequence_length_template": "Mean Read Length",
                "mean_qscore_template": "Mean Mean Qscore",
                "barcode_score": "Mean Barcode Identity",
            }
        )
        df[["Mean Mean Qscore", "Mean Barcode Identity"]] = df[
            ["Mean Mean Qscore", "Mean Barcode Identity"]
        ].applymap(lambda x: flfor(x, 2))
        df[["Mean Read Length"]] = df[["Mean Read Length"]].applymap(
            lambda x: flfor(x, 0)
        )
        fill_colors = conditional_color_range_perCol.discrete_background_color_bins(
            df, 8
        )
    else:
        fill_colors = conditional_color_range_perCol.discrete_background_color_bins(
            df,
            8,
            [
                "PF Clusters",
                "% of thelane",
                "% Perfectbarcode",
                "Yield (Mbases)",
                "% PFClusters",
                "% >= Q30bases",
                "Mean QualityScore",
                "% One mismatchbarcode",
            ],
        )
    table = html.Div(
        [
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                sort_action="native",
                style_data_conditional=fill_colors,
                persistence=True,
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
            )
        ]
    )
    if ont:
        fig = px.pie(df, values="# Reads", names="Sample ID")
    else:
        fig = px.pie(df, values="PF Clusters", names="Sample")
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    fig.update_traces(showlegend=False, textinfo="none")
    return table, fig


def negative_qc_statement(df, negative_list=""):
    if negative_list == "":
        sample_list = list(df["Sample"].unique())
        negative_list = [i for i in sample_list if "PCR" in i]
    df = df.pivot("Sample", columns="Record", values="Reads")
    if "3-altmatch" in df.columns:
        df["Percent Mapping"] = (df["3-match"] + df["3-altmatch"]) / df["1-initial"]
    else:
        df["Percent Mapping"] = df["3-match"] / df["1-initial"]
    statement = [html.Br()]
    for s in negative_list:
        reads_mapping = df.loc[s, "Percent Mapping"] * 100
        if reads_mapping >= 0.01:
            statement.extend(
                [
                    f"You negative sample ",
                    html.Strong(f"{s} FAILS QC ", className="display-7"),
                    f"with {reads_mapping:.2f}% reads mapping to reference.",
                    html.Br(),
                ]
            )
        else:
            statement.extend(
                [
                    f"You negative sample {s} passes QC with {reads_mapping:.2f}% reads mapping to reference.",
                    html.Br(),
                ]
            )
    statement.extend([html.Br()])
    return html.P(statement)


@app.callback(
    [Output("irma_neg_statment", "children"), Output("irma_summary", "children")],
    [
        Input("select_run", "value"),
        Input("samplesheet_table", "data"),
        Input("samplesheet_table", "columns"),
    ],
)
def irma_summary(run, ssrows, sscols):
    if not run or not ssrows or not sscols:
        raise dash.exceptions.PreventUpdate
    ss_df = pd.DataFrame(ssrows, columns=[c["name"] for c in sscols])
    neg_controls = list(ss_df[ss_df["Sample Type"] == "- Control"]["Sample ID"])
    reads = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["read_df"], orient="split"
    )
    qc_statement = negative_qc_statement(reads, neg_controls)
    reads = (
        reads[reads["Record"].str.contains("^1|^2-p|^4")]
        .pivot("Sample", columns="Record", values="Reads")
        .reset_index()
        .melt(id_vars=["Sample", "1-initial", "2-passQC"])
        .rename(
            columns={
                "1-initial": "Total Reads",
                "2-passQC": "Pass QC",
                "Record": "Reference",
                "value": "Reads Mapped",
            }
        )
    )
    reads = reads[~reads["Reads Mapped"].isnull()]
    reads["Reference"] = reads["Reference"].map(lambda x: x[2:])
    reads[["Total Reads", "Pass QC", "Reads Mapped"]] = (
        reads[["Total Reads", "Pass QC", "Reads Mapped"]]
        .astype("int")
        .applymap(lambda x: f"{x:,d}")
    )
    reads = reads[["Sample", "Total Reads", "Pass QC", "Reads Mapped", "Reference"]]
    indels = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["indels_df"], orient="split"
    )
    indels = (
        indels[indels["Frequency"] >= 0.05]
        .groupby(["Sample", "Reference"])
        .agg({"Sample": "count"})
        .rename(columns={"Sample": "Count of Minor Indels >= 0.05"})
        .reset_index()
    )
    alleles = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["alleles_df"], orient="split"
    )
    alleles = (
        alleles[alleles["Minority Frequency"] >= 0.05]
        .groupby(["Sample", "Reference"])
        .agg({"Sample": "count"})
        .rename(columns={"Sample": "Count of Minor SNVs >= 0.05"})
        .reset_index()
    )
    coverage = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["df"], orient="split"
    )
    # Compute the % of reference mapped from IRMAs coverage table and lengths of /intermediate/0-*/0*.ref seq lengths
    ref_lens = json.loads(generate_df(f"{data_root}/{run}"))["ref_lens"]
    cov_ref_lens = (
        coverage[~coverage["Consensus"].isin(["-", "N", "a", "c", "t", "g"])]
        .groupby(["Sample", "Reference_Name"])
        .agg({"Sample": "count"})
        .rename(columns={"Sample": "maplen"})
        .reset_index()
    )

    def perc_len(maplen, ref):
        return maplen / ref_lens[ref] * 100

    cov_ref_lens["% Reference Covered"] = cov_ref_lens.apply(
        lambda x: perc_len(x["maplen"], x["Reference_Name"]), axis=1
    )
    cov_ref_lens["% Reference Covered"] = cov_ref_lens["% Reference Covered"].map(
        lambda x: f"{x:.2f}"
    )
    cov_ref_lens = cov_ref_lens[
        ["Sample", "Reference_Name", "% Reference Covered"]
    ].rename(columns={"Reference_Name": "Reference"})
    coverage = (
        coverage.groupby(["Sample", "Reference_Name"])
        .agg({"Coverage Depth": "mean"})
        .reset_index()
        .rename(
            columns={"Coverage Depth": "Mean Coverage", "Reference_Name": "Reference"}
        )
    )
    coverage[["Mean Coverage"]] = (
        coverage[["Mean Coverage"]].astype("int").applymap(lambda x: f"{x:,d}")
    )
    df = (
        reads.merge(cov_ref_lens, "left")
        .merge(coverage, "left")
        .merge(alleles, "left")
        .merge(indels, "left")
    )
    fill_colors = conditional_color_range_perCol.discrete_background_color_bins(df, 8)
    table = html.Div(
        [
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                sort_action="native",
                style_data_conditional=fill_colors,
                persistence=True,
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
            )
        ]
    )
    return qc_statement, table


@cache.memoize(timeout=cache_timeout)
def create_irma_read_fig(df):
    columns = 12
    rows = 24
    s = '{"type":"domain"} ' * columns
    specs = []
    for i in range(0, rows):
        specs.append([json.loads(a) for a in s.split()])
    fig = make_subplots(rows, columns, specs=specs)
    col_n, row_n = (
        cycle([i for i in range(1, columns + 1)]),
        cycle([i for i in range(1, rows + 1)]),
    )
    counter = 0
    annotations = []
    for sample in set(list(df["Sample"])):
        counter += 1
        if counter % 4 == 1:
            r = next(row_n)
        stage_counter = 0
        for stage in [[2], [3], [4, 5]]:
            c = next(col_n)
            stage_counter += 1
            d2 = df[(df["Stage"].isin(stage)) & (df["Sample"] == sample)]
            fig.add_trace(
                go.Pie(
                    values=d2["Reads"],
                    labels=d2["Record"],
                    name=sample,
                    meta=[sample],
                    hovertemplate="%{meta[0]} <br> %{label} </br> <br> %{percent} </br> %{value} reads <extra></extra> ",
                ),
                row=r,
                col=c,
            )
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=3200,
        hoverlabel=dict(bgcolor="white", font_size=16, namelength=-1),
    )
    fig.update_traces(showlegend=False, textinfo="none")
    return fig


@cache.memoize(timeout=cache_timeout)
def returnSegData(df):
    segments = df["Reference_Name"].unique()
    try:
        segset = [i.split("_")[1] for i in segments]
    except IndexError:
        segset = segments
    segset = list(set(segset))
    segcolor = {}
    for i in range(0, len(segset)):
        segcolor[segset[i]] = px.colors.qualitative.G10[i]
    return segments, segset, segcolor


@cache.memoize(timeout=cache_timeout)
def pivot4heatmap(df):
    if "Coverage_Depth" in df.columns:
        cov_header = "Coverage_Depth"
    else:
        cov_header = "Coverage Depth"
    df2 = df[["Sample", "Reference_Name", cov_header]]
    df3 = df2.groupby(["Sample", "Reference_Name"]).mean().reset_index()
    try:
        df3[["Subtype", "Segment", "Group"]] = df3["Reference_Name"].str.split(
            "_", expand=True
        )
    except ValueError:
        df3["Segment"] = df3["Reference_Name"]
    df4 = df3[["Sample", "Segment", cov_header]]
    return df4


@cache.memoize(timeout=cache_timeout)
def createheatmap(df4, sliderMax=None):
    if "Coverage_Depth" in df4.columns:
        cov_header = "Coverage_Depth"
    else:
        cov_header = "Coverage Depth"
    if sliderMax is None:
        sliderMax = df4[cov_header].max()
    fig = go.Figure(
        data=go.Heatmap(  # px.imshow(df5
            x=list(df4["Sample"]),
            y=list(df4["Segment"]),
            z=list(df4[cov_header]),
            zmin=0,
            zmax=sliderMax,
            colorscale="Blugrn",
            hovertemplate="%{y} = %{z:,.0f}x<extra>%{x}<br></extra>",
        )
    )
    fig.update_layout(legend=dict(x=0.4, y=1.2, orientation="h"))
    fig.update_xaxes(side="top")
    return fig


def createAllCoverageFig(df, segments, segcolor):
    if "Coverage_Depth" in df.columns:
        cov_header = "Coverage_Depth"
    else:
        cov_header = "Coverage Depth"
    samples = df["Sample"].unique()
    fig_numCols = 4
    fig_numRows = ceil(len(samples) / fig_numCols)
    pickCol = cycle(list(range(1, fig_numCols + 1)))  # next(pickCol)
    pickRow = cycle(list(range(1, fig_numRows + 1)))  # next(pickRow)
    # Take every 20th row of data
    df_thin = df.iloc[::20, :]
    fig = make_subplots(
        rows=fig_numRows,
        cols=fig_numCols,
        shared_xaxes="all",
        shared_yaxes=False,
        subplot_titles=(samples),
        vertical_spacing=0.02,
        horizontal_spacing=0.02,
    )
    for s in samples:
        r, c = next(pickRow), next(pickCol)
        for g in segments.split(","):
            try:
                g_base = g.split("_")[1]
            except IndexError:
                g_base = g
            df2 = df_thin[(df_thin["Sample"] == s) & (df_thin["Reference_Name"] == g)]
            fig.add_trace(
                go.Scatter(
                    x=df2["Position"],
                    y=df2[cov_header],
                    mode="lines",
                    line=go.scatter.Line(color=segcolor[g_base]),
                    name=g,
                    customdata=df2["Sample"],
                ),
                row=r,
                col=c,
            )

    def pick_total_height(num_samples):
        if num_samples <= 40:
            return 1200
        else:
            return 2400

    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=pick_total_height(len(samples)),
        showlegend=False,
    )
    return fig


@cache.memoize(timeout=cache_timeout)
def createSampleCoverageFig(sample, df, segments, segcolor, cov_linear_y):
    if "Coverage_Depth" in df.columns:
        cov_header = "Coverage_Depth"
    else:
        cov_header = "Coverage Depth"
    if "HMM_Position" in df.columns:
        pos_header = "HMM_Position"
    else:
        pos_header = "Position"

    def zerolift(x):
        if x == 0:
            return 0.000000000001
        return x

    if not cov_linear_y:
        df[cov_header] = df[cov_header].apply(lambda x: zerolift(x))
    df2 = df[df["Sample"] == sample]
    fig = go.Figure()
    if "SARS-CoV-2" in segments:
        # y positions for gene boxes
        oy = (
            max(df2[cov_header]) / 10
        )  # This value determines where the top of the ORF box is drawn against the y-axis
        if not cov_linear_y:
            ya = 0.9
        else:
            ya = 0 - (max(df2[cov_header]) / 20)
        orf_pos = {
            "orf1ab": (266, 21556),
            "S": [21563, 25385],
            "orf3a": [25393, 26221],
            "E": [26245, 26473],
            "M": [26523, 27192],
            "orf6": [27202, 27388],
            "orf7ab": [27394, 27888],
            "orf8": [27894, 28260],
            "N": [28274, 29534],
            "orf10": [29558, 29675],
        }
        color_index = 0
        for orf, pos in orf_pos.items():
            fig.add_trace(
                go.Scatter(
                    x=[pos[0], pos[1], pos[1], pos[0], pos[0]],
                    y=[oy, oy, 0, 0, oy],
                    fill="toself",
                    fillcolor=px.colors.qualitative.T10[color_index],
                    line=dict(color=px.colors.qualitative.T10[color_index]),
                    mode="lines",
                    name=orf,
                    opacity=0.4,
                )
            )
            color_index += 1
    for g in segments.split(","):
        if g in df2["Reference_Name"].unique():
            try:
                g_base = g.split("_")[1]
            except IndexError:
                g_base = g
            df3 = df2[df2["Reference_Name"] == g]
            fig.add_trace(
                go.Scatter(
                    x=df3[pos_header],
                    y=df3[cov_header],
                    mode="lines",
                    line=go.scatter.Line(color=segcolor[g_base]),
                    name=g,
                    customdata=tuple(["all"] * len(df3["Sample"])),
                )
            )
    fig.add_shape(
        type="line",
        x0=0,
        x1=df2[pos_header].max(),
        y0=100,
        y1=100,
        line=dict(color="Black", dash="dash", width=5),
    )
    ymax = df2[cov_header].max()
    if not cov_linear_y:
        ya_type = "log"
        ymax = ymax ** (1 / 10)
    else:
        ya_type = "linear"
    fig.update_layout(
        height=600,
        title=sample,
        yaxis_title="Coverage",
        xaxis_title="Reference Position",
        yaxis_type=ya_type,
        yaxis_range=[0, ymax],
    )
    return fig


@app.callback(
    Output("coverage-heat", "figure"),
    [Input("heatmap-slider", "value"), Input("select_run", "value")],
)
@cache.memoize(timeout=cache_timeout)
def callback_heatmap(maximumValue, run):
    if not run:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(
        json.loads(generate_df(f"{data_root}/{run}"))["df4"], orient="split"
    )
    # df = pd.read_json(json.loads(data)['df4'], orient='split')
    return createheatmap(df, maximumValue)


@app.callback(
    Output("select_gene", "options"),
    [
        Input("select_machine", "value"),
        Input("select_run", "value"),
        Input("select_irma", "value"),
    ],
)
def select_run(run_path):
    if not run_path:
        raise dash.exceptions.PreventUpdate
    options = [
        {"label": i.split(".")[0], "value": i.split(".")[0]}
        for i in sorted(os.listdir(os.path.join(run_path)))
        if "consensus" not in i and "fasta" in i
    ]  # filesInFolderTree(os.path.join(pathway, machine))]
    return options


@app.callback([Output("select_gene", "value")], Input("select_gene", "options"))
def set_run_options(gene_options):
    if not gene_options:
        raise dash.exceptions.PreventUpdate
    return gene_options[0]["value"]


dl_fasta_clicks = 0


@app.callback(
    Output("download_fasta", "data"),
    [Input("select_run", "value"), Input("fasta_dl_button", "n_clicks")],
    prevent_initial_call=True,
)
def download_fastas(run, n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    global dl_fasta_clicks
    if n_clicks > dl_fasta_clicks:
        dl_fasta_clicks = n_clicks
        return dict(
            content=open(
                f"{data_root}/{run}/IRMA/dais_results/DAIS_ribosome_input.fasta"
            ).read(),
            filename=f"{run}_amended_consensus.fasta",
        )


########################################################
###################### LAYOUT ##########################
########################################################
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "22rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "24rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.Img(src=app.get_asset_url("irma-spy.jpg"), height=80, width=80,),
        html.H2("IRMA Spy", className="display-4"),
        html.P('"Time is a Pony Ride"', className="display-7"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    "Samplesheet", href="#samplesheet_head", external_link=True
                ),
                dbc.NavLink(
                    "Barcode Assignment", href="#demux_head", external_link=True
                ),
                dbc.NavLink("IRMA Summary", href="#irma_head", external_link=True),
                dbc.NavLink(
                    "Reference Coverage", href="#coverage_head", external_link=True
                ),
                dbc.NavLink(
                    "Reference Variants", href="#variants_head", external_link=True
                ),
                dbc.NavLink("Minor SNVs", href="#alleles_head", external_link=True),
                dbc.NavLink("Minor Indels", href="#indels_head", external_link=True),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)


def blank_fig():
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


# import dash_uploader as du
content = html.Div(
    id="page-content",
    style=CONTENT_STYLE,
    children=[
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    id="select_run",
                    options=[
                        {"label": i, "value": i} for i in sorted(os.listdir(data_root))
                    ],
                    placeholder="Select sequencing run: ",
                    # persistence=True
                ),
            )
        )
    ]
    + [html.P("Samplesheet", id="samplesheet_head", className="display-6")]
    + [
        html.Div(
            [
                html.P(
                    "Enter your barcode numbers to be used below:",
                    id="sample_number_info",
                ),
                dcc.Input(
                    id="sample_number",
                    type="text",
                    placeholder="ie. 1-10,15,16,20-29",
                    debounce=True,
                ),
            ]
        )
    ]
    + [html.Br()]
    + [html.Div(id="samplesheet")]
    + [html.Br()]
    + [
        dbc.Row(
            dcc.Dropdown(
                options=["Flu-ONT", "SC2-ONT", "Flu-Illumina"],
                id="experiment_type",
                placeholder="What kind of data is this?",
            )
        )
    ]
    + [
        html.Button("Start Genome Assembly", id="assembly-button", n_clicks=0),
        html.Div(id="output-container-button", children="Hit the button to update."),
    ]
    + [html.P("Barcode Assignment", id="demux_head", className="display-6")]
    + [html.Br()]
    + [
        html.Div(
            [
                dbc.Row(
                    dcc.Loading(
                        id="demux-loading",
                        type="cube",
                        children=[
                            dcc.Graph(id="demux_fig", figure=blank_fig()),
                            html.Div(id="illumina_demux_table"),
                        ],
                    )
                ),
            ]
        )
    ]
    + [html.Br()]
    + [html.P("IRMA Summary", id="irma_head", className="display-6")]
    + [html.Br()]
    + [dbc.Row([html.Div(id="irma_neg_statment"), html.Div(id="irma_summary")])]
    + [html.Br()]
    + [html.P("Reference Coverage", id="coverage_head", className="display-6")]
    + [html.Br()]
    + [
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="coverageheat-loading",
                                type="cube",
                                children=[
                                    dcc.Graph(id="coverage-heat", figure=blank_fig())
                                ],
                            ),
                            width=11,
                            align="end",
                        ),
                        dbc.Col(
                            daq.Slider(
                                id="heatmap-slider",
                                marks={
                                    "100": "100",
                                    "300": "300",
                                    "500": "500",
                                    "700": "700",
                                    "900": "900",
                                },
                                max=1000,
                                min=100,
                                value=100,
                                step=50,
                                vertical=True,
                                persistence=True,
                                dots=True,
                            ),
                            align="center",
                        ),
                    ]  # ,
                    # no_gutters=True
                ),
                dcc.Dropdown(id="select_sample", persistence=True),
                html.Div(id="single_sample_figs"),
                dbc.Col(
                    daq.ToggleSwitch(
                        id="cov_linear_y",
                        label="log y ----- linear y	",
                        labelPosition="bottom",
                        value=True,
                    ),
                    width=8,
                    align="right",
                ),
            ]
        )
    ]
    + [html.Br()]
    + [html.P("Reference Variants", id="variants_head", className="display-6")]
    + [html.Br()]
    + [dbc.Row(html.Div(id="vars_table"))]
    + [html.Br()]
    + [html.P("Minor SNVs", id="alleles_head", className="display-6")]
    + [html.Br()]
    + [dbc.Row(html.Div(id="minor_alleles_table"))]
    + [html.Br()]
    + [
        html.P(
            "Minor Insertions and Deletions", id="indels_head", className="display-6"
        )
    ]
    + [html.Br()]
    + [dbc.Row(html.Div(id="indels_table"))]
    + [html.Br()]
    + [
        html.Div(
            [
                html.Button("Download Fasta", id="fasta_dl_button"),
                dcc.Download(id="download_fasta"),
            ]
        )
    ],
)

app.layout = html.Div([sidebar, content])

####################################################
####################### MAIN #######################
####################################################
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=DEBUG)
