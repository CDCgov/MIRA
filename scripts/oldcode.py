# from cProfile import run
# from symbol import comp_for

# import dash_bio as dbio

# import base64
# import io

# import time

#cache = Cache(
#    app.server,
#    config={
#        "CACHE_TYPE": "filesystem",
#        "CACHE_DIR": f"{data_root}/.cache-directory_fn",
#    },
#)
#cache.clear()

#@callback_cache.memoize(expire=cache_timeout)
#def create_irma_read_fig(df):
#    columns = 12
#    rows = 24
#    s = '{"type":"domain"} ' * columns
#    specs = []
#    for i in range(0, rows):
#        specs.append([json.loads(a) for a in s.split()])
#    fig = make_subplots(rows, columns, specs=specs)
#    col_n, row_n = (
#        cycle([i for i in range(1, columns + 1)]),
#        cycle([i for i in range(1, rows + 1)]),
#    )
#    counter = 0
#    annotations = []
#    for sample in set(list(df["Sample"])):
#        counter += 1
#        if counter % 4 == 1:
#            r = next(row_n)
#        stage_counter = 0
#        for stage in [[2], [3], [4, 5]]:
#            c = next(col_n)
#            stage_counter += 1
#            d2 = df[(df["Stage"].isin(stage)) & (df["Sample"] == sample)]
#            fig.add_trace(
#                go.Pie(
#                    values=d2["Reads"],
#                    labels=d2["Record"],
#                    name=sample,
#                    meta=[sample],
#                    hovertemplate="%{meta[0]} <br> %{label} </br> <br> %{percent} </br> %{value} reads <extra></extra> ",
#                ),
#                row=r,
#                col=c,
#            )
#    fig.update_layout(
#        margin=dict(t=0, b=0, l=0, r=0),
#        height=3200,
#        hoverlabel=dict(bgcolor="white", font_size=16, namelength=-1),
#    )
#    fig.update_traces(showlegend=False, textinfo="none")
#    return fig
#
#
#@callback_cache.memoize(expire=cache_timeout)
#def returnSegData(df):
#    segments = df["Reference_Name"].unique()
#    try:
#        segset = [i.split("_")[1] for i in segments]
#    except IndexError:
#        segset = segments
#    segset = list(set(segset))
#    segcolor = {}
#    for i in range(0, len(segset)):
#        segcolor[segset[i]] = px.colors.qualitative.G10[i]
#    return segments, segset, segcolor


# @callback_cache.memoize(expire=cache_timeout)
#def pivot4heatmap(df):
#    if "Coverage_Depth" in df.columns:
#        cov_header = "Coverage_Depth"
#    else:
#        cov_header = "Coverage Depth"
#    df2 = df[["Sample", "Reference_Name", cov_header]]
#    df3 = df2.groupby(["Sample", "Reference_Name"]).mean().reset_index()
#    try:
#        df3[["Subtype", "Segment", "Group"]] = df3["Reference_Name"].str.split(
#            "_", expand=True
#        )
#    except ValueError:
#        df3["Segment"] = df3["Reference_Name"]
#    df4 = df3[["Sample", "Segment", cov_header]]
#    return df4


# @callback_cache.memoize(expire=cache_timeout)
#def createheatmap(df4):
#    if "Coverage_Depth" in df4.columns:
#        cov_header = "Coverage_Depth"
#    else:
#        cov_header = "Coverage Depth"
#    fig = go.Figure(
#        data=go.Heatmap(  # px.imshow(df5
#            x=list(df4["Sample"]),
#            y=list(df4["Segment"]),
#            z=list(df4[cov_header]),
#            zmin=0,
#            zmax=sliderMax,
#            colorscale="Blugrn",
#            hovertemplate="%{y} = %{z:,.0f}x<extra>%{x}<br></extra>",
#        )
#    )
#    fig.update_layout(legend=dict(x=0.4, y=1.2, orientation="h"))
#    fig.update_xaxes(side="top")
#    return fig


#def createAllCoverageFig(df, segments, segcolor):
#    if "Coverage_Depth" in df.columns:
#        cov_header = "Coverage_Depth"
#    else:
#        cov_header = "Coverage Depth"
#    samples = df["Sample"].unique()
#    fig_numCols = 4
#    fig_numRows = ceil(len(samples) / fig_numCols)
#    pickCol = cycle(list(range(1, fig_numCols + 1)))  # next(pickCol)
#    pickRow = cycle(list(range(1, fig_numRows + 1)))  # next(pickRow)
#    # Take every 20th row of data
#    df_thin = df.iloc[::20, :]
#    fig = make_subplots(
#        rows=fig_numRows,
#        cols=fig_numCols,
#        shared_xaxes="all",
#        shared_yaxes=False,
#        subplot_titles=(samples),
#        vertical_spacing=0.02,
#        horizontal_spacing=0.02,
#    )
#    for s in samples:
#        r, c = next(pickRow), next(pickCol)
#        for g in segments.split(","):
#            try:
#                g_base = g.split("_")[1]
#            except IndexError:
#                g_base = g
#            df2 = df_thin[(df_thin["Sample"] == s) & (df_thin["Reference_Name"] == g)]
#            fig.add_trace(
#                go.Scatter(
#                    x=df2["Position"],
#                    y=df2[cov_header],
#                    mode="lines",
#                    line=go.scatter.Line(color=segcolor[g_base]),
#                    name=g,
#                    customdata=df2["Sample"],
#                ),
#                row=r,
#                col=c,
#            )

#    def pick_total_height(num_samples):
#        if num_samples <= 40:
#            return 1200
#        else:
#            return 2400
#
#    fig.update_layout(
#        margin=dict(l=0, r=0, t=40, b=0),
#        height=pick_total_height(len(samples)),
#        showlegend=False,
#    )
#    return fig


#@callback_cache.memoize(expire=cache_timeout)
#def createSampleCoverageFig(sample, df, segments, segcolor, cov_linear_y):
#    if "Coverage_Depth" in df.columns:
#        cov_header = "Coverage_Depth"
#    else:
#        cov_header = "Coverage Depth"
#    if "HMM_Position" in df.columns:
#        pos_header = "HMM_Position"
#    else:
#        pos_header = "Position"
#
#    def zerolift(x):
#        if x == 0:
#            return 0.000000000001
#        return x
#
#    if cov_linear_y:
#        df[cov_header] = df[cov_header].apply(lambda x: zerolift(x))
#    df2 = df[df["Sample"] == sample]
#    fig = go.Figure()
#    if "SARS-CoV-2" in segments:
#        # y positions for gene boxes
#        oy = (
#            max(df2[cov_header]) / 10
#        )  # This value determines where the top of the ORF box is drawn against the y-axis
#        if not cov_linear_y:
#            ya = 0.9
#        else:
#            ya = 0 - (max(df2[cov_header]) / 20)
#        orf_pos = {
#            "orf1ab": (266, 21556),
#            "S": [21563, 25385],
#            "orf3a": [25393, 26221],
#            "E": [26245, 26473],
#            "M": [26523, 27192],
#            "orf6": [27202, 27388],
#            "orf7ab": [27394, 27888],
#            "orf8": [27894, 28260],
#            "N": [28274, 29534],
#            "orf10": [29558, 29675],
#        }
#        color_index = 0
#        for orf, pos in orf_pos.items():
#            fig.add_trace(
#                go.Scatter(
#                    x=[pos[0], pos[1], pos[1], pos[0], pos[0]],
#                    y=[oy, oy, 0, 0, oy],
#                    fill="toself",
#                    fillcolor=px.colors.qualitative.T10[color_index],
#                    line=dict(color=px.colors.qualitative.T10[color_index]),
#                    mode="lines",
#                    name=orf,
#                    opacity=0.4,
#                )
#            )
#            color_index += 1
#    for g in segments.split(","):
#        if g in df2["Reference_Name"].unique():
#            try:
#                g_base = g.split("_")[1]
#            except IndexError:
#                g_base = g
#            df3 = df2[df2["Reference_Name"] == g]
#            fig.add_trace(
#                go.Scatter(
#                    x=df3[pos_header],
#                    y=df3[cov_header],
#                    mode="lines",
#                    line=go.scatter.Line(color=segcolor[g_base]),
#                    name=g,
#                    customdata=tuple(["all"] * len(df3["Sample"])),
#                )
#            )
#    fig.add_shape(
#        type="line",
#        x0=0,
#        x1=df2[pos_header].max(),
#        y0=100,
#        y1=100,
#        line=dict(color="Black", dash="dash", width=5),
#    )
#    ymax = df2[cov_header].max()
#    if not cov_linear_y:
#        ya_type = "log"
#        ymax = ymax ** (1 / 10)
#    else:
#        ya_type = "linear"
#    fig.update_layout(
#        height=600,
#        title=sample,
#        yaxis_title="Coverage",
#        xaxis_title="Reference Position",
#        yaxis_type=ya_type,
#        yaxis_range=[0, ymax],
#    )
#    return fig

#def callback_heatmap(run):
#    if not run:
#        return blank_fig()
#        #raise dash.exceptions.PreventUpdate
#    try:
#        return pio.read_json(f"{data_root}/{run}/IRMA/heatmap.json")
#    except FileNotFoundError:
#        return blank_fig()
    # df = pd.read_json(
    #    json.loads(generate_df(f"{data_root}/{run}"))["df4"], orient="split"
    # )
    # except:
    #    raise dash.exceptions.PreventUpdate
    # df = pd.read_json(json.loads(data)['df4'], orient='split')
    #return createheatmap(df, maximumValue)

    
#@app.callback(
#    Output("select_gene", "options"),
#    [
#        Input("select_machine", "value"),
#        Input("select_run", "value"),
#        Input("select_irma", "value"),
#    ],
#)
#def select_run(run_path):
#    if not run_path:
#        raise dash.exceptions.PreventUpdate
#    options = [
#        {"label": i.split(".")[0], "value": i.split(".")[0]}
#        for i in sorted(os.listdir(os.path.join(run_path)))
#        if "consensus" not in i and "fasta" in i
#    ]  # filesInFolderTree(os.path.join(pathway, machine))]
#    return options
#
#
#@app.callback([Output("select_gene", "value")], Input("select_gene", "options"))
#def set_run_options(gene_options):
#    if not gene_options:
#        raise dash.exceptions.PreventUpdate
#    return gene_options[0]["value"]

#def download_fastas(run, n_clicks):
#    if not n_clicks:
#        raise dash.exceptions.PreventUpdate
#    global dl_fasta_clicks
#    if n_clicks > dl_fasta_clicks:
#        dl_fasta_clicks = n_clicks
#        #if "sc2" in exp_type.lower():
#        content = open(
#            f"{data_root}/{run}/IRMA/dais_results/DAIS_ribosome_input.fasta"
#        ).read()
        #else:
        #    fastas = glob(f"{data_root}/{run}/IRMA/*/*fasta")
        #    flu_type = {}
        #    for fasta in fastas:
        #        sample = fasta.split("/")[-2]
        #        flu_type[sample] = fasta.split("/")[-1].split("_")[0]
        #        # print(f"fasta={fasta}; sample={sample}; flu_type={flu_type[sample]}")
        #    content = []
        #    with open(
        #        f"{data_root}/{run}/IRMA/dais_results/DAIS_ribosome_input.fasta", "r"
        #    ) as d:
        #        for line in d:
        #            line = line.strip()
        #            if line[0] == ">":
        #                sample = line[1:-2]
        #                seg_num = line[-1]
        #                line = f">{sample}_{flu_numbers[flu_type[sample]][seg_num]}"
        #                content.append(line)
        #            else:
        #                content.append(line)

        #    content = "\n".join(content)
#        return dict(
#            content=content,
#            filename=f"{run}_amended_consensus.fasta",
#        )
#