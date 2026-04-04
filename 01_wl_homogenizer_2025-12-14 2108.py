# Imports for OSX plotting only:
import matplotlib
matplotlib.use('TkAgg')
# - END -

import pandas as pd
from modules.WaterLevelHomogenizer import WaterLevelHomogenizer


def debug_baselevel_value(df, base_lvl_date, label=""):
    dt_check = pd.to_datetime(base_lvl_date)
    # Find closest matching datetime in df
    nearest_idx = df['datetime'].sub(dt_check).abs().idxmin()
    v_at_base = df.loc[nearest_idx, 'wl_final']
    print(f"{label} | Calibration timestamp: {dt_check} | Nearest df timestamp: {df.loc[nearest_idx, 'datetime']} | wl_final: {v_at_base}")


h = WaterLevelHomogenizer("00_params_simple_2025-12-11T1003.yml")

# stations = ["KG_G354-new","KG_G354-old", "KG_BS-old","KG_BS-new1","KG_BS-new2", "KG_Arabel"]
# stations = ["KG_Abramov-left"]
stations = ["KG_Abramov-right"]
for station in stations:
    # station = "KG_BS-old"
    print(f"################### {station} ###################")
    years = list(h.get_station_info(station)['base_levels'].keys())
    for year in years:
        df_final = h.process_year(station, year)
        if df_final is not None:
        #     h.write_to_csv(df_final,f"test_{station}_{year}.csv")
              h.plot_ts_single_year(station,year)


h.results
# station = "KG_Abramov-left"
station = "KG_Abramov-right"

cat_df = h.concatenate_series_with_baselevel(station=station)
# cat_df = h.ensure_hourly_continuous(cat_df) # Not needed
h.write_to_csv(cat_df, f"/Users/pohle/Dropbox/Central_Asia/DISCHARGE/L3/{station}_cat_df.csv")
h.plot_ts_multi_years(h,cat_df, station)
# plt.close()

#
# def process_year(h, station_key, year, subselection=None):
#     # TESTS
# info = h.get_station_info(station_key)
#
# water_files = h.get_file_list(station_key, "wl")
# atmo_files = h.get_file_list(station_key, "atmo")
#
# year_str = str(year)
# search_string = info.get("searchstring")  # "left"/"right" or None
#
# # Important: filter only water by search_string
# water_file = h.select_files(
#     water_files, year_str, "water", search_string=search_string
# )
# atmo_file = h.select_files(
#     atmo_files, year_str, "atmo"
# )
#
# if water_file is None:
#     print(f"SKIP: No water file for {station_key}, {year_str}")
#     return None
# if atmo_file is None:
#     print(f"SKIP: No atmo file for {station_key}, {year_str}")
#     return None
#
# water_full_path = h.main_data_path / info["wl_folder"] / water_file
# atmo_full_path = h.main_data_path / info["atmo_folder"] / atmo_file
#
# df_wl = h.read_with_timezone(water_full_path)
# df_atmo = h.read_with_timezone(atmo_full_path)
#
# h.df_corr = h.correct_water_level(df_wl, df_atmo)
# h.df_final = h.adjust_base_level(h.df_corr, station_key, year)
# h.results[station_key, int(year)] = h.df_final
#
