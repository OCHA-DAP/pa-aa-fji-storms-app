import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dcc, html

import datasources

cod2 = datasources.load_codab(2)
fms = datasources.load_cyclonetracks()
trigger_zone = datasources.load_buffer(250)
trigger_zone = trigger_zone.to_crs(datasources.FJI_CRS)

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
                    fms["Name Season"].unique(),
                    "Yasa 2020/2021",
                    id="dropdown-selection",
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
    dff = cod2.copy()
    dff = dff.to_crs(datasources.FJI_CRS)
    dff = dff.set_index("ADM2_PCODE")
    nameyear = fms[fms["Name Season"] == name_season].iloc[0]["nameyear"]
    ac_f = fms[fms["nameyear"] == nameyear].copy()
    ac_f["simple_date"] = ac_f["datetime"].apply(
        lambda x: x.strftime("%b %d, %H:%M")
    )
    fig = px.choropleth_mapbox(
        dff,
        geojson=dff.geometry,
        locations=dff.index,
    )
    x, y = trigger_zone.geometry[0].boundary.xy
    fig.add_trace(
        go.Scattermapbox(
            lat=np.array(y),
            lon=np.array(x),
            mode="lines",
            name="Area within 250km of Fiji",
            line=dict(width=1, color="dodgerblue"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        # mapbox_accesstoken=os.getenv("MB_TOKEN"),
        mapbox_zoom=5.5,
        mapbox_center_lat=-17,
        mapbox_center_lon=179,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        # title=f"{name_season}<br>" f"<sup>{subtitle}</sup>",
    )
    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
