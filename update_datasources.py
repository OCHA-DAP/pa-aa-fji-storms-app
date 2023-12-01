import os
import shutil
from pathlib import Path

DATA_DIR = Path(os.getenv("AA_DATA_DIR"))
PROC_REL_DIR = Path("public") / "processed" / "fji"
RAW_REL_DIR = Path("public") / "raw" / "fji"

CODAB_REL_PATH = RAW_REL_DIR / "cod_ab"
ADM2_REL_PATH = CODAB_REL_PATH / "fji_polbnda_adm2_province"
BUFFER_REL_PATH = PROC_REL_DIR / "buffer" / "fji_250km_buffer"
FMS_TRACKS_REL_PATH = PROC_REL_DIR / "fms_tracks_processed.csv"
FMS_FORECASTS_REL_PATH = PROC_REL_DIR / "fms_historical_forecasts.csv"
ECMWF_PROCESSED_REL_PATH = (
    Path("public")
    / "exploration"
    / "fji"
    / "ecmwf"
    / "cyclone_hindcasts"
    / "besttrack_forecasts.csv"
)
APP_DATA_DIR = Path("data")


def update_datasources():
    """Copy data from Google Drive into this repo.
    The folder structure in the APP_DATA_DIR is kept the same as in the
    Google Drive, to make things easier to load.
    """
    rel_paths = [
        ECMWF_PROCESSED_REL_PATH,
        FMS_TRACKS_REL_PATH,
        FMS_FORECASTS_REL_PATH,
        ADM2_REL_PATH,
        BUFFER_REL_PATH,
    ]
    for rel_path in rel_paths:
        old_path = DATA_DIR / rel_path
        new_path = APP_DATA_DIR / rel_path
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        if old_path.is_dir():
            shutil.copytree(old_path, new_path, dirs_exist_ok=True)
        else:
            shutil.copy(old_path, new_path)


if __name__ == "__main__":
    update_datasources()
