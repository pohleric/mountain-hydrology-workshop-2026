from pathlib import Path
import pandas as pd
import numpy as np


def write_to_csv(dataset: pd.DataFrame, output_filename):
    """
    Write a dataframe with a tz-aware 'datetime' column to CSV using ISO timestamps.
    """
    output_path = Path(output_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_out = dataset.copy()
    df_out["datetime"] = df_out["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    df_out["datetime"] = df_out["datetime"].str.replace(
        r"([+-]\d{2})(\d{2})$", r"\1:\2", regex=True
    )
    df_out.to_csv(output_path, index=False)


def write_wl_with_iso_tz(df: pd.DataFrame, out_path):
    """
    Write a water-level dataframe whose datetime is stored in the index.
    """
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    out = df.copy()
    out = out.reset_index().rename(columns={"index": "datetime"})
    out["datetime"] = out["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    out["datetime"] = out["datetime"].str.replace(
        r"([+-]\d{2})(\d{2})$", r"\1:\2", regex=True
    )
    out.to_csv(output_path, index=False)


def merge_wl_q(
    station: str,
    filename_wl=None,
    filename_q=None,
    filename_out=None,
    filename_out_mini=None,
    wl_sheet_name: str = "clean",
    q_time_tolerance: str = "30min",
    write_outputs: bool = True,
):
    """
    Merge one station's water-level series with discharge measurements.

    Parameters
    ----------
    station : str
        Station name, e.g. 'KG_G354-new'.
    filename_wl : str | Path | None
        Input CSV of concatenated water level.
        Default:
        ./DISCHARGE/L3/{station}_cat_df.csv
    filename_q : str | Path | None
        Input Excel file with discharge data.
        Default:
        ./DISCHARGE/Q-FL/{station}_Q-FL.xlsx
    filename_out : str | Path | None
        Output CSV for the full WL time series with ISO UTC timestamps.
        Default:
        ./DISCHARGE/L3/{station}_cat_df_withQv2.csv
    filename_out_mini : str | Path | None
        Output CSV for rows where both WL and Q are available.
        Default:
        ./DISCHARGE/L3/{station}_cat_df_WL-Q.csv
    wl_sheet_name : str
        Excel sheet name for discharge data. Default: 'clean'
    q_time_tolerance : str
        Time window used around the WL period. Default: '30min'
    write_outputs : bool
        Whether to write output files. Default: True

    Returns
    -------
    result : pd.DataFrame
        Full merged dataframe after filtering invalid WL rows.
    result_filtered : pd.DataFrame
        Only rows where both WL and Q are available.
    """

    base_dir = Path.cwd() / "DISCHARGE"
    filename_wl = Path(filename_wl) if filename_wl is not None else base_dir / "L3" / f"{station}_cat_df.csv"
    filename_q = Path(filename_q) if filename_q is not None else base_dir / "Q-FL" / f"{station}_Q-FL.xlsx"
    filename_out = Path(filename_out) if filename_out is not None else base_dir / "L3" / f"{station}_cat_df_withQv2.csv"
    filename_out_mini = Path(filename_out_mini) if filename_out_mini is not None else base_dir / "L3" / f"{station}_cat_df_WL-Q.csv"

    if not filename_wl.exists():
        raise FileNotFoundError(f"Water-level input file not found: {filename_wl}")
    if not filename_q.exists():
        raise FileNotFoundError(f"Discharge input file not found: {filename_q}")

    # 1) Read hourly water-level data
    df = pd.read_csv(filename_wl)
    if "datetime" not in df.columns:
        raise KeyError(f"'datetime' column not found in water-level file: {filename_wl}")
    if "wl_final" not in df.columns:
        raise KeyError(f"'wl_final' column not found in water-level file: {filename_wl}")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()

    start_date = df.index.min()
    end_date = df.index.max()

    # 2) Read and clean discharge data
    q = pd.read_excel(filename_q, sheet_name=wl_sheet_name)
    q = q.replace("", pd.NA)

    required_q_cols = [
        "date",
        "time (UTC+0)",
        "discharge (calc) [m3/s]",
        "discharge (calc with extrapolation) [m3/s]",
    ]
    missing_q_cols = [c for c in required_q_cols if c not in q.columns]
    if missing_q_cols:
        raise KeyError(
            f"Missing required column(s) in discharge file {filename_q}: {missing_q_cols}"
        )

    q = q.dropna(
        subset=[
            "discharge (calc) [m3/s]",
            "discharge (calc with extrapolation) [m3/s]",
        ],
        how="all",
    )

    q["dt_utc"] = pd.to_datetime(
        q["date"].astype(str) + "T" + q["time (UTC+0)"].astype(str),
        format="%Y-%m-%dT%H:%M:%S",
        utc=True,
    )

    q["discharge"] = q[
        ["discharge (calc) [m3/s]", "discharge (calc with extrapolation) [m3/s]"]
    ].mean(axis=1)

    tol = pd.Timedelta(q_time_tolerance)
    mask_q = (
        q["dt_utc"].dt.year.isin(df.index.year.unique())
        & (q["dt_utc"] >= start_date - tol)
        & (q["dt_utc"] <= end_date + tol)
    )

    q = q.loc[mask_q].set_index("dt_utc").sort_index()
    q = q.dropna(subset=["discharge"])

    # 3) Merge and interpolate onto combined time index
    new_index = df.index.union(q.index).sort_values()
    df_interp = df.reindex(new_index).interpolate(method="time")

    # Put measured discharges at their timestamps
    df_interp["discharge"] = q["discharge"]

    result = df_interp.reset_index().rename(columns={"index": "datetime"})

    # 4) If first WL timestep has NaN discharge, fill with mean of discharge
    #    values within tolerance before it
    result = result.sort_values("datetime").reset_index(drop=True)

    pre_mask = (
        (result["datetime"] < start_date)
        & (result["datetime"] >= start_date - tol)
        & (~result["discharge"].isna())
    )
    pre_vals = result.loc[pre_mask, "discharge"]

    if not pre_vals.empty:
        pre_mean = pre_vals.mean()
        idx_start = result.index[result["datetime"] == start_date]
        if len(idx_start) == 1:
            idx_start = idx_start[0]
            if pd.isna(result.at[idx_start, "discharge"]):
                result.at[idx_start, "discharge"] = pre_mean

    # 5) Drop rows where no water level exists
    result = result.loc[~result["wl_final"].isna()].copy()

    # Replace non-positive WL values with NA
    result.loc[result["wl_final"] <= 0, "wl_final"] = np.nan

    # Only with entries where WL and Q are available
    result_filtered = result.loc[
        ~result["discharge"].isna() & ~result["wl_final"].isna()
    ].copy()

    # 6) Export
    if write_outputs:
        write_wl_with_iso_tz(df, filename_out)
        write_to_csv(result_filtered, filename_out_mini)
        print(f"Output written to: {filename_out.resolve()}")
        print(f"Output written to: {filename_out_mini.resolve()}")

    return result, result_filtered


if __name__ == "__main__":
    # Example run
    merge_wl_q("KG_G354-new")
