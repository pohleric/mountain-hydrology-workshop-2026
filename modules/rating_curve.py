from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def ensure_parent_dir(path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def make_H0_grid_from_data(H0_min: float, H0_max: float, n: int = 200) -> np.ndarray:
    return np.linspace(H0_min, H0_max, n)


@dataclass
class RatingCurveParams:
    H0: float
    a: float
    b: float


class RatingCurve:
    """
    Power-law rating curve: Q = a * (H - H0)**b
    """

    def __init__(self, params: RatingCurveParams, rel_q_uncertainty: float = 0.3):
        self.params = params
        self.rel_q_uncertainty = rel_q_uncertainty

    @staticmethod
    def _fit_for_fixed_H0(
        H: np.ndarray,
        Q: np.ndarray,
        H0: float,
        min_valid_frac: float = 0.8,
    ) -> Optional[RatingCurveParams]:
        x = H - H0
        mask = (x > 0) & (Q > 0)
        valid_frac = mask.mean()

        if valid_frac < min_valid_frac or mask.sum() < 3:
            return None

        x_log = np.log(x[mask])
        y_log = np.log(Q[mask])

        A = np.vstack([x_log, np.ones_like(x_log)]).T
        b, c = np.linalg.lstsq(A, y_log, rcond=None)[0]
        a = float(np.exp(c))

        return RatingCurveParams(H0=H0, a=a, b=float(b))

    @staticmethod
    def fit_from_dataframe(
        df: pd.DataFrame,
        h_col: str = "wl_final",
        q_col: str = "discharge",
        H0_grid: Optional[np.ndarray] = None,
        rel_q_uncertainty: float = 0.3,
        min_valid_frac: float = 0.8,
    ) -> "RatingCurve":
        H = df[h_col].to_numpy(dtype=float)
        Q = df[q_col].to_numpy(dtype=float)

        H_min = np.nanmin(H)
        H_max = np.nanmax(H)

        if H0_grid is None:
            delta = max(0.05 * (H_max - H_min), 0.2)
            eps = 0.01
            H0_low = H_min - delta
            H0_high = H_min - eps
            H0_grid = np.linspace(H0_low, H0_high, 40)

        best_params: Optional[RatingCurveParams] = None
        best_ssr = np.inf

        for H0 in H0_grid:
            params = RatingCurve._fit_for_fixed_H0(
                H, Q, H0, min_valid_frac=min_valid_frac
            )
            if params is None:
                continue

            x = H - params.H0
            mask = (x > 0) & (Q > 0)
            x_log = np.log(x[mask])
            y_log = np.log(Q[mask])
            y_pred = params.b * x_log + np.log(params.a)

            ssr = float(np.sum((y_log - y_pred) ** 2))

            if ssr < best_ssr:
                best_ssr = ssr
                best_params = params

        if best_params is None:
            raise ValueError("Could not fit rating curve with given constraints.")

        return RatingCurve(best_params, rel_q_uncertainty=rel_q_uncertainty)

    def predict(self, H: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        H = np.asarray(H, dtype=float)
        x = H - self.params.H0
        Q_mid = self.params.a * np.maximum(x, 0.0) ** self.params.b

        factor = self.rel_q_uncertainty
        Q_low = Q_mid * (1.0 - factor)
        Q_high = Q_mid * (1.0 + factor)
        return Q_mid, Q_low, Q_high

    def __call__(self, H: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.predict(H)

    def plot_fit(
        self,
        df: pd.DataFrame,
        h_col: str = "wl_final",
        q_col: str = "discharge",
        ax: Optional[plt.Axes] = None,
        n_points: int = 100,
        loglog: bool = False,
        station: Optional[str] = None,
        show_point_errors: bool = True,
    ):
        if ax is None:
            fig, ax = plt.subplots()

        H_obs = df[h_col].to_numpy(float)
        Q_obs = df[q_col].to_numpy(float)

        H_min, H_max = np.nanmin(H_obs), np.nanmax(H_obs)
        H_grid = np.linspace(H_min, H_max, n_points)
        Q_mid, Q_low, Q_high = self.predict(H_grid)

        ax.scatter(H_obs, Q_obs, s=20, alpha=0.7, label="gauging points")

        if show_point_errors:
            q_err = self.rel_q_uncertainty * Q_obs
            ax.errorbar(
                H_obs,
                Q_obs,
                yerr=q_err,
                fmt="none",
                ecolor="gray",
                elinewidth=1,
                capsize=2,
                alpha=0.7,
            )

        ax.plot(H_grid, Q_mid, label="rating curve")
        ax.fill_between(H_grid, Q_low, Q_high, alpha=0.2, label="±uncertainty")

        ax.set_xlabel("Water level [cm]")
        ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")

        if loglog:
            ax.set_xscale("log")
            ax.set_yscale("log")

        title = "Rating curve fit"
        if station is not None:
            title += f" – {station}"
        ax.set_title(title)
        ax.legend()
        return ax



def plot_station_year_timeseries(
    station: str,
    year: int,
    df_year: pd.DataFrame,
    figure_dir,
    show_plot: bool = True,
):
    df = df_year.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    t = df["datetime"]
    q_mid = df["Q_mid"]
    q_low = df["Q_low"]
    q_high = df["Q_high"]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, q_mid, label="Q_mid", linewidth=0.4)
    ax.fill_between(t, q_low, q_high, alpha=0.2, label="Q_low / Q_high")

    ax.set_xlabel("Time")
    ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")
    ax.set_title(f"{station} – discharge time series {year}")
    ax.legend()
    fig.autofmt_xdate()

    out_path = ensure_parent_dir(Path(figure_dir) / f"{station}_timeseries_{year}.pdf")
    fig.savefig(out_path, bbox_inches="tight")
    print(f"Figure written to: {out_path.resolve()}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def plot_station_all_years_timeseries(
    station: str,
    all_year_dfs: List[pd.DataFrame],
    figure_dir,
    show_plot: bool = True,
):
    if not all_year_dfs:
        return

    df = pd.concat(all_year_dfs, ignore_index=True)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    t = df["datetime"]
    q_mid = df["Q_mid"]
    q_low = df["Q_low"]
    q_high = df["Q_high"]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t, q_mid, label="Q_mid", linewidth=0.4)
    ax.fill_between(t, q_low, q_high, alpha=0.2, label="Q_low / Q_high")

    ax.set_xlabel("Time")
    ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")
    ax.set_title(f"{station} – discharge time series (all years)")
    ax.legend()
    fig.autofmt_xdate()

    out_path = ensure_parent_dir(Path(figure_dir) / f"{station}_timeseries_all-years.pdf")
    fig.savefig(out_path, bbox_inches="tight")
    print(f"Figure written to: {out_path.resolve()}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def _default_h0_bounds_min() -> Dict[str, float]:
    return {
        "KG_G354-new": -10.0,
        "KG_G354-old": -30.0,
        "KG_BS-old": -15.0,
        "KG_BS-new": -15.0,
        "KG_Arabel": -25.0,
        "KG_Abramov-left": -35.0,
        "KG_Abramov-right": -15.0,
    }


def _default_h0_bounds_max() -> Dict[str, float]:
    return {
        "KG_G354-new": 15.0,
        "KG_G354-old": 5.0,
        "KG_BS-old": 0.0,
        "KG_BS-new": 0.0,
        "KG_Arabel": 15.0,
        "KG_Abramov-left": 5.0,
        "KG_Abramov-right": 10.0,
    }


def process_station_rating_curve(
    station: str,
    filename_full=None,
    filename_mini=None,
    output_dir=None,
    figure_dir=None,
    H0_min: Optional[float] = None,
    H0_max: Optional[float] = None,
    min_points: int = 5,
    rel_q_uncertainty: float = 0.3,
    min_valid_frac: float = 0.5,
    save_clean_copy: bool = True,
    plot_yearly_rating_curves: bool = True,
    plot_yearly_timeseries: bool = True,
    plot_all_years_timeseries: bool = True,
    show_plots: bool = True,
):
    """
    Process one station from L3 WL-Q data to L4 rating-curve outputs.

    Default input:
    - ./DISCHARGE/L3/{station}_cat_df_withQv2.csv
    - ./DISCHARGE/L3/{station}_cat_df_WL-Q.csv

    Default output:
    - ./DISCHARGE/L4/
    - ./DISCHARGE/figures/

    H0_min and H0_max are single-station bounds. If omitted, station-specific
    defaults are used when available.
    """
    base_dir = Path.cwd() / "DISCHARGE"
    filename_full = Path(filename_full) if filename_full is not None else base_dir / "L3" / f"{station}_cat_df_withQv2.csv"
    filename_mini = Path(filename_mini) if filename_mini is not None else base_dir / "L3" / f"{station}_cat_df_WL-Q.csv"
    output_dir = Path(output_dir) if output_dir is not None else base_dir / "L4"
    figure_dir = Path(figure_dir) if figure_dir is not None else base_dir / "figures"

    if not filename_full.exists():
        raise FileNotFoundError(f"Full WL-Q input file not found: {filename_full}")
    if not filename_mini.exists():
        raise FileNotFoundError(f"Mini WL-Q input file not found: {filename_mini}")

    wl_q_df_full = pd.read_csv(filename_full)
    wl_q_df_mini = pd.read_csv(filename_mini)

    if "datetime" not in wl_q_df_full.columns:
        raise KeyError(f"'datetime' column not found in file: {filename_full}")
    if "datetime" not in wl_q_df_mini.columns:
        raise KeyError(f"'datetime' column not found in file: {filename_mini}")
    if "wl_final" not in wl_q_df_full.columns:
        raise KeyError(f"'wl_final' column not found in file: {filename_full}")
    if "wl_final" not in wl_q_df_mini.columns:
        raise KeyError(f"'wl_final' column not found in file: {filename_mini}")
    if "discharge" not in wl_q_df_mini.columns:
        raise KeyError(f"'discharge' column not found in file: {filename_mini}")

    wl_q_df_full["datetime"] = pd.to_datetime(wl_q_df_full["datetime"])
    wl_q_df_mini["datetime"] = pd.to_datetime(wl_q_df_mini["datetime"])

    wl_q_df_full["year"] = wl_q_df_full["datetime"].dt.year
    wl_q_df_mini["year"] = wl_q_df_mini["datetime"].dt.year

    years = sorted(int(y) for y in wl_q_df_full["year"].unique())

    default_h0_min = _default_h0_bounds_min().get(station, None)
    default_h0_max = _default_h0_bounds_max().get(station, None)

    if H0_min is None:
        H0_min = default_h0_min
    if H0_max is None:
        H0_max = default_h0_max

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    last_curve: Optional[RatingCurve] = None
    year_dfs: List[pd.DataFrame] = []
    written_files: List[Path] = []

    print(f"Processing station: {station}")
    print(f"Input full file: {filename_full.resolve()}")
    print(f"Input mini file: {filename_mini.resolve()}")
    print(f"H0_min: {H0_min}")
    print(f"H0_max: {H0_max}")

    for year in years:
        df_year_pairs = wl_q_df_mini[wl_q_df_mini["year"] == year].copy()
        df_year_full = wl_q_df_full[wl_q_df_full["year"] == year].copy()

        if df_year_full.empty:
            continue

        curve: Optional[RatingCurve] = None

        if len(df_year_pairs) >= min_points:
            wl_min_flow = df_year_full["wl_final"].min()

            if H0_max is None:
                H0_max_year = wl_min_flow
            else:
                H0_max_year = min(H0_max, wl_min_flow)

            if H0_min is None:
                H0_min_year = H0_max_year - 40.0
            else:
                H0_min_year = H0_min

            H0_grid = np.linspace(H0_min_year, H0_max_year, 200)

            try:
                curve = RatingCurve.fit_from_dataframe(
                    df_year_pairs,
                    h_col="wl_final",
                    q_col="discharge",
                    rel_q_uncertainty=rel_q_uncertainty,
                    min_valid_frac=min_valid_frac,
                    H0_grid=H0_grid,
                )
                last_curve = curve
            except ValueError:
                curve = last_curve
        else:
            curve = last_curve

        if curve is None:
            print(f"Skip year {year}: no curve could be assigned.")
            continue

        if plot_yearly_rating_curves and not df_year_pairs.empty:
            fig, ax = plt.subplots()
            curve.plot_fit(
                df_year_pairs,
                ax=ax,
                loglog=False,
                station=f"{station} {year}",
            )
            fig_path = ensure_parent_dir(figure_dir / f"{station}_rating-curve_{year}.pdf")
            fig.savefig(fig_path, bbox_inches="tight")
            print(f"Figure written to: {fig_path.resolve()}")

            if show_plots:
                plt.show()
            else:
                plt.close(fig)

        H = df_year_full["wl_final"].to_numpy(float)
        Q_mid, Q_low, Q_high = curve.predict(H)

        df_out = df_year_full.copy()
        df_out["Q_mid"] = Q_mid
        df_out["Q_low"] = Q_low
        df_out["Q_high"] = Q_high

        df_out["datetime"] = pd.to_datetime(df_out["datetime"])
        if getattr(df_out["datetime"].dt, "tz", None) is not None:
            dt_utc = df_out["datetime"].dt.tz_convert("UTC")
        else:
            dt_utc = df_out["datetime"]
        df_out["datetime"] = dt_utc.dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        if "year" in df_out.columns:
            df_out.drop(columns="year", inplace=True)

        out_path = ensure_parent_dir(output_dir / f"{station}_{year}_wl_q_data.csv")
        df_out.to_csv(out_path, index=False)
        written_files.append(out_path)
        print(f"Output written to: {out_path.resolve()}")

        if save_clean_copy:
            df_out_nice = df_out.rename(columns={
                "datetime": "datetime (UTC+0)",
                "pressure": "pressure_water (cmH2O)",
                "temp": "temperature_water (deg.C)",
                "pressure_atmo": "pressure_atmo (cmH2O)",
                "temp_atmo": "temperature_atmo (deg.C)",
                "wl_corr": "wl_corr (cmH2O)",
                "wl_final": "wl_final (cmH2O)",
                "Q_mid": "Q_mid (m^3 s^{-1})",
                "Q_low": "Q_low (m^3 s^{-1})",
                "Q_high": "Q_high (m^3 s^{-1})",
            })
            out_path_nice = ensure_parent_dir(output_dir / f"{station}_{year}_wl_q_data_clean.csv")
            df_out_nice.to_csv(out_path_nice, index=False)
            written_files.append(out_path_nice)
            print(f"Output written to: {out_path_nice.resolve()}")

        year_df_for_plot = pd.read_csv(out_path)
        year_dfs.append(year_df_for_plot)

        if plot_yearly_timeseries:
            plot_station_year_timeseries(
                station,
                year,
                year_df_for_plot,
                figure_dir,
                show_plot=show_plots,
            )

    if plot_all_years_timeseries:
        plot_station_all_years_timeseries(
            station,
            year_dfs,
            figure_dir,
            show_plot=show_plots,
        )

    return {
        "station": station,
        "years": years,
        "H0_min": H0_min,
        "H0_max": H0_max,
        "written_files": [str(p.resolve()) for p in written_files],
        "output_dir": str(output_dir.resolve()),
        "figure_dir": str(figure_dir.resolve()),
    }


if __name__ == "__main__":
    process_station_rating_curve("KG_G354-new")
