# Imports for OSX plotting only:
import matplotlib

matplotlib.use('TkAgg')
# - END -

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt

# t: 1D numpy array of time points
# y: 1D numpy array of noisy signal
colnames = ["date",	"time",	"time_adj","Tracer1",	"Battery",	"Baseline",	"Temperature"]
# x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/noise_signal_test.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20210822_1403l_repair_abramov-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220725_1500_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220725_1700_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220726_0800_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220726_0700_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220726_0900_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20230725_0930_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20230725_1100_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20230725_1300_repair_abra-left.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220725_1120_repair_abra-right.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220725_1300_repair_abra-right.csv", names=colnames)
x = pd.read_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220726_0700_repair_abra-right.csv", names=colnames)

x['datetime'] = pd.to_datetime(x['date']+ "T" +x['time_adj'])


df = x.set_index('datetime')
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

dt_index = df.index.to_numpy()
t0 = dt_index[0]
t_sec = (dt_index - t0) / np.timedelta64(1, "s")

y = df["Tracer1"].to_numpy()   # or your fluorescence column

# 1) Optionally smooth slightly to reduce tiny spikes
from scipy.ndimage import uniform_filter1d
# y_smooth = uniform_filter1d(y, size=10)  # small window, keeps main shape
y_smooth = uniform_filter1d(y, size=10)  # small window, keeps main shape

# 2) Find peaks (tune these parameters!)
peaks, props = find_peaks(
    y,
    distance=10,          # minimum samples between peaks (~6 s for 2 s step)
    prominence=.1      # ignore very small spikes; tune to your scale
)
t_peaks = t_sec[peaks]
y_peaks = y[peaks]       # use original height for envelope


# Fit a smoothing spline only through peak points
# Use fewer knots by increasing s or using k=3 (cubic)
spline_env = UnivariateSpline(t_peaks, y_peaks, s=len(t_peaks), k=3)
y_envelope = spline_env(t_sec)

# Plot
plt.figure(figsize=(10, 4))
plt.plot(df.index, y, color="grey", label="noisy signal")
plt.plot(df.index, y_envelope, color="red", linewidth=2, label="upper envelope")
plt.plot(df.index[peaks], y_peaks, "ko", ms=3, label="peaks used")
plt.legend()
plt.tight_layout()
plt.show()

df['splined_peaks'] = y_envelope
df.to_csv("/Users/pohle/Dropbox/Central_Asia/DISCHARGE/Q-FL/20220726_0700_repair_abra-right-splined.csv")
