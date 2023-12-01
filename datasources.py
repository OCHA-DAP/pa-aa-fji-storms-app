from pathlib import Path

import geopandas as gpd
import pandas as pd

APP_DATA_DIR = Path("data")
RAW_DIR = APP_DATA_DIR / "public" / "raw" / "fji"
CODAB_PATH = RAW_DIR / "cod_ab"
PROC_PATH = APP_DATA_DIR / "public" / "processed" / "fji"

FJI_CRS = "+proj=longlat +ellps=WGS84 +lon_wrap=180 +datum=WGS84 +no_defs"


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
