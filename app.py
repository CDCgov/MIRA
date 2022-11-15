# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from cProfile import run
from symbol import comp_for
import dash
from dash import dcc, dash_table, html, DiskcacheManager, ctx
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
import diskcache

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

# Fucntion caching
cache_timeout = 60 * 60 * 24 * 28
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": f"{data_root}/.cache-directory_fn",
    },
)
cache.clear()

# Callback caching
callback_cache = diskcache.Cache(f"{data_root}/.cache-directory_cb")
bkgnd_callback_manager = DiskcacheManager(callback_cache)


previousClick = 0


@app.callback(Output("select_run", "options"), Input("run-refresh-button", "n_clicks"))
def refreshRuns(n_clicks):
    options = [
        {"label": i, "value": i} for i in sorted(os.listdir(data_root)) if "." not in i
    ]
    return options


@app.callback(
    [Output("select_sample", "options"), Output("select_sample", "value")],
    [Input("coverage-heat", "clickData"), Input("select_run", "value")],
)
@cache.memoize(timeout=cache_timeout)
def select_sample(plotClick, run):
    if not run:
        raise dash.exceptions.PreventUpdate
    try:
        df = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["df4"], orient="split"
        )
    except:
        raise dash.exceptions.PreventUpdate
    samples = df["Sample"].unique()
    samples.sort()
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
        Input("irma-results-button", "n_clicks"),
    ],
)
@cache.memoize(timeout=cache_timeout)
def single_sample_fig(run, sample, cov_linear_y, n_clicks):
    if not run or not sample:
        return html.Div()
        # raise dash.exceptions.PreventUpdate
    if not n_clicks:
        return html.Div()
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
    ss_glob = [
        i
        for i in glob(f"{data_root}/{run}/*.csv*")
        if "samplesheet" in i.lower() or "data" in i.lower()
    ]
    if len(ss_glob) == 1:
        ss_filename = ss_glob[0]
        with open(ss_filename, "rb") as d:
            originalByteList = d.readlines()
        noCarriageReturn = "".join(
            [i.decode().replace("\r", "") for i in originalByteList]
        )
        with open(ss_filename, "w") as d:
            d.write(noCarriageReturn)
        data = pd.read_csv(ss_filename).to_dict("records")
    elif not sample_number:
        raise dash.exceptions.PreventUpdate
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


# @cache.memoize(timeout=cache_timeout)
@app.callback(
    Output("output-container-button", "children"),
    [
        Input("assembly-button", "n_clicks"),
        Input("select_run", "value"),
        Input("experiment_type", "value"),
    ],
    background=True,
    manager=bkgnd_callback_manager,
)
def run_snake_script_onClick(n_clicks, run, experiment_type):
    if not n_clicks:
        # raise dash.exceptions.PreventUpdate
        return dash.no_update
    if not run:
        raise dash.exceptions.PreventUpdate
    if not experiment_type:
        raise dash.exceptions.PreventUpdate

    docker_cmd = "docker exec -w /data sc2-spike-seq bash snake-kickoff "
    docker_cmd += f"/data/{run}/samplesheet.csv "
    docker_cmd += f"/data/{run} "
    docker_cmd += experiment_type
    print(f'launching docker_cmd == "{docker_cmd}"\n\n')
    # result = subprocess.check_output(docker_cmd, shell=True)
    result = subprocess.Popen(docker_cmd.split(), stdout=subprocess.PIPE)
    out, err = result.communicate()
    # convert bytes to string
    result = f"STDOUT == {out}{html.Br()}STDERR == {err}"
    print(f"... and the result == {result}\n\n")
    return html.Div("IRMA finished!")  # result


@app.callback(
    Output("irma-progress", "children"),
    [
        Input("select_run", "value"),
        Input("watch-irma-progress", "value"),
        Input("irma-progress-interval", "n_intervals"),
    ],
)
def display_irma_progress(run, toggle, n_intervals):
    if not toggle:
        return html.Div()
    logs = glob(f"{data_root}/{run}/logs/*irma*out.log")
    if len(logs) == 0:
        return html.Div("No IRMA data is available")
    log_dic = {}
    for l in logs:
        sample = l.split("/")[-1].split(".")[0]
        with open(l, "r") as d:
            log_dic[sample] = "".join(d.readlines())
    finished_samples = [i for i in log_dic.keys() if "finished!" in log_dic[i].lower()]
    running_samples = {
        i: f"  ".join(j.split("\t"))
        for i, j in log_dic.items()
        if i not in finished_samples
    }
    if len(running_samples.keys()) == 0:
        return html.Div("IRMA has finished running")
    df = pd.DataFrame.from_dict(running_samples, orient="index")
    df = df.reset_index()
    df.columns = ["Sample", "IRMA Stage"]
    out = html.Div(
        [
            html.Div(f"IRMA finished samples: {', '.join(finished_samples)}"),
            html.Div(
                # [dbc.Row(
                # [dbc.Col(
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict("records"),
                    style_cell={
                        "whiteSpace": "pre-line",
                        "height": "auto",
                        "lineHeight": "15px",
                        "text_align": "left",
                    },
                )
                # , width={"size":4, "offset":0})])]
            ),
        ]
    )
    return out


def flfor(x, digits):
    return float(f"{x:.{digits}f}")


@app.callback(
    [
        Output("minor_alleles_table", "children"),
        [Input("select_run", "value"), Input("irma-results-button", "n_clicks")],
    ]
)
def alleles_table(run, n_clicks):
    if not run:
        raise dash.exceptions.PreventUpdate
    if not n_clicks:
        dash.exceptions.PreventUpdate
    try:
        df = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["alleles_df"], orient="split"
        )
    except:
        raise dash.exceptions.PreventUpdate
        # return blank_fig()
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


@app.callback(
    [
        Output("indels_table", "children"),
        [Input("select_run", "value"), Input("irma-results-button", "n_clicks")],
    ]
)
def indels_table(run, n_clicks):
    if not run:
        raise dash.exceptions.PreventUpdate
    if not n_clicks:
        dash.exceptions.PreventUpdate
    try:
        df = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["indels_df"], orient="split"
        )
    except:
        raise dash.exceptions.PreventUpdate
        # return blank_fig()
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


@app.callback(
    [
        Output("vars_table", "children"),
        [Input("select_run", "value"), Input("irma-results-button", "n_clicks")],
    ]
)
def vars_table(run, n_clicks):
    if not run:
        raise dash.exceptions.PreventUpdate
    if not n_clicks:
        dash.exceptions.PreventUpdate
    try:
        df = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["dais_vars"], orient="split"
        )
    except:
        raise dash.exceptions.PreventUpdate
        # return blank_fig()
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


@app.callback(
    [Output("illumina_demux_table", "children"), Output("demux_fig", "figure")],
    [
        Input("select_run", "value"),
    ],
    prevent_initial_call=True,
    background=True,
    manager=bkgnd_callback_manager,
)
@cache.memoize(timeout=cache_timeout)
def demux_table(run):
    glob_files = [
        f
        for f_ in [
            glob(n)
            for n in [
                f"{data_root}/{run}/sequencing_summary*txt",
                f"{data_root}/{run}/laneBarcode.html",
            ]
        ]
        for f in f_
    ]
    try:
        print(f"start reading {glob_files[0]}")
    except:
        return blank_fig(), blank_fig()
    ont = False
    if len(glob_files) == 1:
        if "sequencing_summary" in glob_files[0]:
            ont = True
            rc = sum(1 for row in open(glob_files[0]))

            def f(g):
                return pd.DataFrame(
                    {
                        "# Reads": [g.shape[0]],
                        "read_len_sum": [g["sequence_length_template"].sum()],
                        "mean_q_sum": [g["mean_qscore_template"].sum()],
                        "mean_barid_sum": [g["barcode_score"].sum()],
                    }
                )

            df = pd.DataFrame({})
            chunksize = 50000
            chunknum = chunksize
            reader = pd.read_csv(
                glob_files[0],
                chunksize=chunksize,
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
            for chunk in reader:
                df = df.add(
                    chunk.groupby(["barcode_arrangement"])
                    .apply(f)
                    .reset_index(level=1, drop=True),
                    fill_value=0,
                )
                print(f"rc = {rc} chunksize = {chunknum}")
                print(f"Reading {glob_files[0]} :: {float(chunknum)/float(rc)*100}%")
                chunknum += chunksize
            df = df.reset_index()
            df["Mean Read Length"] = df["read_len_sum"] / df["# Reads"]
            df["Mean Mean Qscore"] = df["mean_q_sum"] / df["# Reads"]
            df["Mean Barcode Identity"] = df["mean_barid_sum"] / df["# Reads"]
            df = df.rename(columns={"barcode_arrangement": "Barcode"})
            df = df[
                [
                    "Barcode",
                    "# Reads",
                    "Mean Read Length",
                    "Mean Mean Qscore",
                    "Mean Barcode Identity",
                ]
            ]
            df[["Mean Mean Qscore", "Mean Barcode Identity"]] = df[
                ["Mean Mean Qscore", "Mean Barcode Identity"]
            ].applymap(lambda x: flfor(x, 2))
            df[["# Reads", "Mean Read Length"]] = df[
                ["# Reads", "Mean Read Length"]
            ].applymap(lambda x: int(x))
        else:
            df = pd.read_html(glob_files[0])[2]
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
                # persistence=True,
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
                filter_action="native",
            )
        ]
    )
    if ont:
        fig = px.pie(df, values="# Reads", names="Barcode")
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
        Input("irma-results-button", "n_clicks"),
    ],
)
def irma_summary(run, ssrows, sscols, n_clicks):
    if not run or not ssrows or not sscols:
        raise dash.exceptions.PreventUpdate
    ss_df = pd.DataFrame(ssrows, columns=[c["name"] for c in sscols])
    neg_controls = list(ss_df[ss_df["Sample Type"] == "- Control"]["Sample ID"])
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        reads = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["read_df"], orient="split"
        )
    except:
        # raise dash.exceptions.PreventUpdate
        return "... waiting for IRMA results...", html.Div()
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
                # persistence=True,
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
                filter_action="native",
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


# @cache.memoize(timeout=cache_timeout)
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


# @cache.memoize(timeout=cache_timeout)
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
    try:
        df = pd.read_json(
            json.loads(generate_df(f"{data_root}/{run}"))["df4"], orient="split"
        )
    except:
        raise dash.exceptions.PreventUpdate
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

flu_numbers = {
    "A": {
        "1": "PB2",
        "2": "PB1",
        "3": "PA",
        "4": "HA",
        "5": "NP",
        "6": "NA",
        "7": "MP",
        "8": "NS",
    },
    "B": {
        "1": "PB1",
        "2": "PB2",
        "3": "PA",
        "4": "HA",
        "5": "NP",
        "6": "NA",
        "7": "MP",
        "8": "NS",
    },
}


@app.callback(
    Output("download_fasta", "data"),
    [
        Input("select_run", "value"),
        Input("fasta_dl_button", "n_clicks"),
        Input("experiment_type", "value"),
    ],
    prevent_initial_call=True,
)
def download_fastas(run, n_clicks, exp_type):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    global dl_fasta_clicks
    if n_clicks > dl_fasta_clicks:
        dl_fasta_clicks = n_clicks
        if "sc2" in exp_type.lower():
            content = open(
                f"{data_root}/{run}/IRMA/dais_results/DAIS_ribosome_input.fasta"
            ).read()
        else:
            fastas = glob(f"{data_root}/{run}/IRMA/*/*fasta")
            flu_type = {}
            for fasta in fastas:
                sample = fasta.split("/")[-2]
                flu_type[sample] = fasta.split("/")[-1].split("_")[0]
            content = []
            with open(
                f"{data_root}/{run}/IRMA/dais_results/DAIS_ribosome_input.fasta", "r"
            ) as d:
                for line in d:
                    line = line.strip()
                    try:
                        if line[0] == ">":
                            sample = line[1:-2]
                            seg_num = line[-1]
                            line = f">{sample}_{flu_numbers[flu_type[sample]][seg_num]}"
                            content.append(line)
                        else:
                            content.append(line)
                    except KeyError:
                        pass
            content = "\n".join(content)
        return dict(
            content=content,
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
        html.Img(
            src=app.get_asset_url("irma-spy.jpg"),
            height=80,
            width=80,
        ),
        html.H2("IRMA SPY", className="display-4"),
        html.P(
            ["Sequences", html.Br(), "Prepared by", html.Br(), "You"],
            className="display-7",
        ),
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
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="select_run",
                        options=[
                            {"label": i, "value": i}
                            for i in sorted(os.listdir(data_root))
                            if "." not in i
                        ],
                        placeholder="Select sequencing run: ",
                        persistence=True,
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Button(
                        "Refresh Run Listing", id="run-refresh-button", n_clicks=0
                    )
                ),
            ]
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
                persistence=True,
            )
        )
    ]
    + [
        html.Button("Start Genome Assembly", id="assembly-button", n_clicks=0),
        html.Div(id="output-container-button"),
        dcc.Interval(id="irma-progress-interval", interval=3000),
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        daq.ToggleSwitch(
                            id="watch-irma-progress",
                            label="Watch IRMA progress",
                            labelPosition="right",
                            value=False,
                        ),
                        width=2,
                    )
                )
            ]
        ),
        html.Div(id="irma-progress"),
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
    + [
        html.Div(
            html.Button("Display IRMA results", id="irma-results-button", n_clicks=0),
        )
    ]
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
