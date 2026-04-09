require(readxl)
require(lubridate)
require(MESS)

# - reading FL30 raw data
# - transforming data into readable format with signal in mV

# Arguments
path = "~/work/mountain-hydrology-workshop-2026/Fluorometer/KG_G354"

Standard = 50        # g/l - The concentration of the color tracer (Standard solution)
TracerVolume = 0.1  # l - How many liters! were injected into the river?
# bucketvolume is FIXED to 5 L

# ---- 2021 -----
# Input file (Excel)
filename_excel = '2021 - Measurements_G354.xlsx'

# ---- 
sheet_name = '20210928_1052'    
TracerVolume = .02
sheet_name = '20210928_1220_cleaned'
TracerVolume = .025
sheet_name = '20210928_1310'    
TracerVolume = .04
sheet_name = '20210928_1409'    
TracerVolume = .06
sheet_name = '20210928_1510_cleaned'
TracerVolume = .12
sheet_name = '20210928_1600'  
TracerVolume = .12



# ------------ NO NEED TO CHANGE ANYTHING HEREAFTER --------------- #
# gc() # This cleans the memory - against JAVA Problems ...
setwd(path)
# source('../R/FUN_install_packages.R')
M = Standard * TracerVolume * 1000 # to mg
# Source all functions for cleaning and preparation
source('../0_R-FUN/FUN_curve-processing-fixedCalibrationLiquid.R')

# ------- READ DATA ------- #
# d_ = read.xlsx(sheetName = sheet_name,  # this one needs to be changed to read in the different sheets,
#                file = filename_excel, 
#                header = F)
library(lubridate)
d_ = read_xlsx_(filename = filename_excel,sheet = sheet_name)

# ---- remove NAs and visual check
d_ = rm_nas(d_)
plot(d_$X1, d_$X4, type='l')
require(zoo)
ttt = na.approx(d_$X4)
d_$X4 = ttt
lines(d_$X1, ttt, col='red')
d_ = na.omit(d_)
# ---- Make date-time
tmp_date = make_date_time(d_)

# ---- Combine data
d = data.frame(date=tmp_date, Tracer1=d_$X4)

# ---- Noise removal
d = remove_noise(d)

# ---- Calibration
calibrate(d, 1, 600)

# ---- Relationship mV to ppb
d = relate_mV_ppb(d)


# ---- Discharge Calculation --------- #
# Calculate discharge with the global method
# ppb = 1 µg/L
# Q = M/A
# - M [mg] = 1000 µg
# - A [µg*s / L]
# ->
# L*1000/s = m3/s
# ---------------------------------------- #


# ---- Curve 1 
calc_discharge(d)


# ---- Curve 2 
# If second (overlapping) breakthrough curve exists:
print("Is there a second breakthrough curve (with overlap)?")

# Was the same amount of tracer used? --> Change if yes!
# ----- Change the following two Arguments if need be ---------------------------- #
Standard = Standard          # g/l - The concentration of the color tracer (Standard solution)
TracerVolume = TracerVolume  # l - How many liters! were injected into the river?
# -------------------------------------------------------------------------------- #
M = Standard * TracerVolume * 1000 

# calc_discharge_overlap(d, dss)


