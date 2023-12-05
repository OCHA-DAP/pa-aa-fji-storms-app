from pathlib import Path

import geopandas as gpd
import pandas as pd

APP_DATA_DIR = Path("data")
RAW_DIR = APP_DATA_DIR / "public" / "raw" / "fji"
CODAB_PATH = RAW_DIR / "cod_ab"
PROC_PATH = APP_DATA_DIR / "public" / "processed" / "fji"
ECMWF_PROCESSED = (
    APP_DATA_DIR
    / "public"
    / "exploration"
    / "fji"
    / "ecmwf"
    / "cyclone_hindcasts"
)

FJI_CRS = "+proj=longlat +ellps=WGS84 +lon_wrap=180 +datum=WGS84 +no_defs"


def knots2cat(knots: float) -> int:
    """
    Convert from knots to Category (Australian scale)
    Parameters
    ----------
    knots: float
        Wind speed in knots

    Returns
    -------
    Category
    """
    category = 0
    if knots > 107:
        category = 5
    elif knots > 85:
        category = 4
    elif knots > 63:
        category = 3
    elif knots > 47:
        category = 2
    elif knots > 33:
        category = 1
    return category


def load_cyclonetracks() -> gpd.GeoDataFrame:
    df = pd.read_csv(PROC_PATH / "fms_tracks_processed.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    gdf_tracks = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"])
    )
    gdf_tracks.crs = "EPSG:4326"
    return gdf_tracks


def load_codab(level: int = 2) -> gpd.GeoDataFrame:
    """
    Load Fiji codab
    Note: there seems to be a problem with level=2 (province)

    Parameters
    ----------
    level: int = 3
        admin level

    Returns
    -------
    gdf: gpd.GeoDataFrame
        includes setting CRS EPSG:3832
    """
    adm_name = ""
    if level == 0:
        adm_name = "country"
    elif level == 1:
        adm_name = "district"
    elif level == 2:
        adm_name = "province"
    elif level == 3:
        adm_name = "tikina"
    filename = f"fji_polbnda_adm{level}_{adm_name}"
    gdf = gpd.read_file(CODAB_PATH / filename, layer=filename).set_crs(3832)
    if level > 0:
        gdf["ADM1_NAME"] = gdf["ADM1_NAME"].replace(
            "Northern  Division", "Northern Division"
        )
    return gdf


def load_buffer(distance: int = 250) -> gpd.GeoDataFrame:
    """
    Load buffer file

    Parameters
    ----------
    distance: int = 250
        Distance from adm0 in km

    Returns
    -------

    """
    filename = f"fji_{distance}km_buffer"
    load_path = PROC_PATH / "buffer" / filename / f"{filename}.shp"

    return gpd.read_file(load_path)


def load_historical_triggers() -> pd.DataFrame:
    df = pd.read_csv(PROC_PATH / "historical_triggers.csv")
    cols = [
        "ec_3day_date",
        "ec_5day_date",
        "fms_fcast_date",
        "fms_actual_date",
    ]
    for col in cols:
        df[col] = pd.to_datetime(df[col])
    return df


def load_hindcasts() -> gpd.GeoDataFrame:
    """
    Loads RSMC / FMS hindcasts
    Returns
    -------
    gdf of hindcasts
    """
    date_cols = ["time", "base_time"]
    filename = "fms_historical_forecasts.csv"
    df = pd.read_csv(PROC_PATH / filename, parse_dates=date_cols)
    df = df.rename(columns={"time": "forecast_time"})

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"])
    )
    gdf.crs = "EPSG:4326"

    return gdf


def load_ecmwf_besttrack_hindcasts():
    df = pd.read_csv(ECMWF_PROCESSED / "besttrack_forecasts.csv")
    cols = ["time", "forecast_time"]
    for col in cols:
        df[col] = pd.to_datetime(df[col])
    gdf = gpd.GeoDataFrame(
        data=df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"], crs="EPSG:4326"),
    )
    gdf = gdf.to_crs(FJI_CRS)
    return gdf
