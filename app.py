import json
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import shapely
from dash import Dash, Input, Output, callback, dcc, html
from shapely import LineString

import datasources

INIT_NAMESEASON = "Yasa 2020/2021"

start = time.time()

# LOAD FILES
cod2 = datasources.load_codab(2)
fms = datasources.load_cyclonetracks()
hindcasts = datasources.load_hindcasts()
ecmwf = datasources.load_ecmwf_besttrack_hindcasts()
trigger_zone = datasources.load_buffer(250)
trigger_zone = trigger_zone.to_crs(datasources.FJI_CRS)
triggers = datasources.load_historical_triggers()
triggers = triggers.set_index("nameyear")

cod2 = cod2.to_crs(datasources.FJI_CRS)
cod2 = cod2.rename(columns={"ADM2_NAME": "Province"})
cod2 = cod2.set_index("Province")

ecmwf["forecast_time"] = pd.to_datetime(ecmwf["forecast_time"])
ecmwf["fms_speed"] = ecmwf["speed_knots"] * 0.940729 + 14.9982
ecmwf["fms_cat"] = ecmwf["fms_speed"].apply(datasources.knots2cat)

print(f"load: {time.time() - start:.3f}")
start = time.time()
# init_fig = px.choropleth_mapbox(
#     cod2,
#     geojson=cod2.geometry,
#     locations=cod2.index,
# )
# init_fig.update_traces(name="Provinces", marker_opacity=0.5)
init_fig = px.choropleth_mapbox()
print(f"codab: {time.time() - start:.3f}")
start = time.time()

# plot trigger zone
x, y = trigger_zone.geometry[0].boundary.xy
init_fig.add_trace(
    go.Scattermapbox(
        lat=np.array(y),
        lon=np.array(x),
        mode="lines",
        name="Area within 250km of Fiji",
        line=dict(width=1, color="dodgerblue"),
        hoverinfo="skip",
        # showlegend=False,
    )
)


# SET UP APP
app = Dash(__name__)
server = app.server
app.layout = html.Div(
    [
        html.Div(
            id="left-sidebar",
            className="mt-4 ml-4",
            style={
                "position": "fixed",
                "width": "200px",
                "top": 10,
                "left": 10,
                "zIndex": 1,
            },
            children=[
                dcc.Dropdown(
                    fms.sort_values("datetime", ascending=False)[
                        "Name Season"
                    ].unique(),
                    INIT_NAMESEASON,
                    id="dropdown-selection",
                    clearable=False,
                ),
            ],
        ),
        html.Div(
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "zIndex": "0",
            },
            children=dcc.Graph(
                id="graph-content",
                style={"height": "100vh", "background-color": "#f8f9fc"},
                config={"displayModeBar": False},
            ),
        ),
    ]
)


@callback(
    Output("graph-content", "figure"), Input("dropdown-selection", "value")
)
def update_graph(name_season):
    start = time.time()

    def gdf_buffers(gdf):
        ls = LineString(gdf.geometry.to_crs(3832))
        polys = []
        distances = [50, 100, 200]
        # prev_poly = None
        for d in distances:
            poly = ls.buffer(d * 1000)
            for prev_poly in polys:
                poly = shapely.difference(poly, prev_poly)
            polys.append(poly)

        buffers = gpd.GeoDataFrame(
            data=distances, geometry=polys, crs=3832
        ).to_crs(datasources.FJI_CRS)
        buffers = buffers.rename(columns={0: "distance"})
        return buffers

    name = name_season.split(" ")[0]
    nameyear = fms[fms["Name Season"] == name_season].iloc[0]["nameyear"]
    trigger = triggers.loc[nameyear]
    ac_f = fms[fms["nameyear"] == nameyear].copy()
    ac_f["simple_date"] = ac_f["datetime"].apply(
        lambda x: x.strftime("%b %d, %H:%M")
    )
    fm_f = (
        hindcasts[hindcasts["nameyear"] == nameyear]
        .sort_values("base_time")
        .copy()
    )
    fm_f["cat_str"] = fm_f["Category"].apply(lambda x: str(x).split(".")[0])
    ec_f = (
        ecmwf[ecmwf["nameyear"] == nameyear]
        .sort_values("forecast_time")
        .copy()
    )
    print(f"filter: {time.time() - start:.3f}")
    start = time.time()

    # plot CODAB
    # fig = px.choropleth_mapbox(
    #     cod2,
    #     geojson=cod2.geometry,
    #     locations=cod2.index,
    # )
    # fig.update_traces(name="Provinces", marker_opacity=0.5)
    # print(f"codab: {time.time() - start:.3f}")
    # start = time.time()
    #
    # # plot trigger zone
    # x, y = trigger_zone.geometry[0].boundary.xy
    # fig.add_trace(
    #     go.Scattermapbox(
    #         lat=np.array(y),
    #         lon=np.array(x),
    #         mode="lines",
    #         name="Area within 250km of Fiji",
    #         line=dict(width=1, color="dodgerblue"),
    #         hoverinfo="skip",
    #         # showlegend=False,
    #     )
    # )
    fig = go.Figure(init_fig)
    print(f"trig_zone: {time.time() - start:.3f}")
    start = time.time()

    # plot actual path
    fig.add_trace(
        go.Scattermapbox(
            lon=ac_f["Longitude"],
            lat=ac_f["Latitude"],
            mode="lines+text",
            text=ac_f["Category"],
            textfont=dict(size=20, color="black"),
            line=dict(color="black", width=2),
            marker=dict(size=5),
            name=f"Actual - {name}",
            customdata=ac_f[["Category numeric", "simple_date"]],
            hovertemplate="Category: %{customdata[0]}<br>"
            "Datetime: %{customdata[1]}",
            legendgroup="actual",
            legendgrouptitle_text="",
            visible="legendonly",
        )
    )
    print(f"path: {time.time() - start:.3f}")
    start = time.time()
    # plot actual buffers
    buffers = gdf_buffers(ac_f)

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=json.loads(buffers.geometry.to_json()),
            locations=buffers.index,
            z=buffers["distance"],
            marker_opacity=0.3,
            marker_line_width=0,
            colorscale="YlOrRd_r",
            name="50/100/200km buffer",
            legendgroup="actual",
            showlegend=False,
            showscale=False,
            zmin=50,
            zmid=200,
            zmax=250,
            hoverinfo="skip",
            visible="legendonly",
        )
    )
    print(f"path_buf: {time.time() - start:.3f}")
    start = time.time()

    # FMS forecasts
    for base_time in fm_f["base_time"].unique():
        if base_time == trigger["fms_fcast_date"]:
            act = "A: "
        else:
            act = ""
        date_str = base_time.strftime("%b %d, %H:%M")
        dff = fm_f[fm_f["base_time"] == base_time]
        dff = dff.sort_values("forecast_time")
        fig.add_trace(
            go.Scattermapbox(
                lon=dff["Longitude"],
                lat=dff["Latitude"],
                mode="text+lines",
                text=dff["cat_str"],
                textfont=dict(size=20, color="black"),
                line=dict(width=2),
                marker=dict(size=10),
                name=act + date_str,
                customdata=dff[["Category", "forecast_time"]],
                hovertemplate="Category: %{customdata[0]}<br>"
                "Datetime: %{customdata[1]}",
                legendgroup=date_str,
                legendgrouptitle_text="",
                visible="legendonly",
            )
        )

        buffers = gdf_buffers(dff)
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=json.loads(buffers.geometry.to_json()),
                locations=buffers.index,
                z=buffers["distance"],
                marker_opacity=0.3,
                marker_line_width=0,
                colorscale="YlOrRd_r",
                legendgroup=date_str,
                name="50/100/200km buffer",
                showlegend=False,
                showscale=False,
                zmin=50,
                zmid=200,
                zmax=250,
                hoverinfo="skip",
                visible="legendonly",
            )
        )
    print(f"fms: {time.time() - start:.3f}")
    start = time.time()

    # EC forecasts
    if fm_f.empty:
        line = dict(width=2)
        colorscale = "YlOrRd_r"
    else:
        line = dict(width=2, color="grey")
        colorscale = "Greys_r"
    for base_time in ec_f["forecast_time"].unique():
        if base_time == trigger["ec_5day_date"]:
            red = "R: "
        else:
            red = ""
        if base_time == trigger["ec_3day_date"] and fm_f.empty:
            act = "A: "
        else:
            act = ""
        date_str = base_time.strftime("%b %d, %H:%M")
        dff = ec_f[ec_f["forecast_time"] == base_time]
        dff = dff.sort_values("time")
        fig.add_trace(
            go.Scattermapbox(
                lon=dff["lon"],
                lat=dff["lat"],
                mode="text+lines",
                text=dff["fms_cat"].astype(str),
                textfont=dict(size=20, color="black"),
                line=line,
                marker=dict(size=5),
                name=f"{red}{act} EC {date_str}",
                customdata=dff[["fms_cat", "time"]],
                hovertemplate="Category: %{customdata[0]}<br>"
                "Datetime: %{customdata[1]}",
                legendgroup=f"EC {date_str}",
                legendgrouptitle_text="",
                visible="legendonly",
            )
        )

        buffers = gdf_buffers(dff)
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=json.loads(buffers.geometry.to_json()),
                locations=buffers.index,
                z=buffers["distance"],
                marker_opacity=0.3,
                marker_line_width=0,
                colorscale=colorscale,
                legendgroup=f"EC {date_str}",
                name="50/100/200km buffer",
                showlegend=False,
                showscale=False,
                zmin=50,
                zmid=200,
                zmax=250,
                hoverinfo="skip",
                visible="legendonly",
            )
        )
    print(f"ec: {time.time() - start:.3f}")
    start = time.time()

    if fm_f.empty:
        if ec_f.empty:
            legend_title = ""
        else:
            legend_title = "ECMWF 120hr forecasts in colour"
    else:
        legend_title = (
            "FMS 72hr forecasts in colour;<br>" "ECMWF 120hr forecasts in grey"
        )
    if trigger["ec_5day_trig"]:
        legend_title += ";<br>R: Readiness"
    if trigger["fms_fcast_trig"] or trigger["ec_3day_trig"]:
        legend_title += ";<br>A: Action"

    fig.update_layout(
        mapbox_style="open-street-map",
        # mapbox_accesstoken=os.getenv("MB_TOKEN"),
        mapbox_zoom=5.5,
        mapbox_center_lat=-17,
        mapbox_center_lon=179,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        # title=f"{name_season}<br>" f"<sup>{subtitle}</sup>",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255,255,255,0.5)",
            title=legend_title,
        ),
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
