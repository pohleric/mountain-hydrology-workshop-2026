# require(xlsx)
# require('openxlsx')
require(readxl)
require(lubridate)
require(MESS)

# - reading FL30 raw data
# - transforming data into readable format with signal in mV

# Arguments
path = "~/work/mountain-hydrology-workshop-2026/Fluorometer/KG_G354"
setwd(path)

Standard = 196.388        # g/l - The concentration of the color tracer (Standard or Base solution)

# ---- Read data -----
# Input file (Excel)
filename_excel = '2025 - Measurements_Abramov-glacier.xlsx'

# ---- Individual measurements -----
# Adjust here the prepared spreadsheet name in the Excel file and fill in the numbers from the calibration preparation




# 23 July 8:42 ----------------------------------------------------------------------
# R side 
# Adjust this for each individual measurement
sheet_name = '20250723_0842_r'  
TracerMass = 40.36    # g - How many grams of the tracer liquid were injected into the river?
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 12.22           # g - measured in gramms
m_calib_solution2 = 10.68           # g - measured in gramms
m_calib_solution3 = 10.73           # g - measured in gramms
m_calib_solution4 = NULL            # if not performed --> NULL


# 23 July 9:33 ----------------------------------------------------------------------
# L side
sheet_name = '20250723_0933_l'  
TracerMass = 58.02    # g - How many grams of the tracer liquid were injected into the river?
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 11.10           # g - measured in gramms
m_calib_solution2 = 12.00           # g - measured in gramms
m_calib_solution3 = 11.93           # g - measured in gramms
m_calib_solution4 = NULL            # if not performed --> NULL



# 23 July 10:18 ----------------------------------------------------------------------
# R side 
sheet_name = '20250723_1018_r'  
TracerMass =  49.41   # g - How many grams of the tracer liquid were injected into the river?
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 12.16
m_calib_solution2 = 12.14
m_calib_solution3 = 13.53
m_calib_solution4 = NULL           


# 23 July 11:30 ----------------------------------------------------------------------
# R side 
sheet_name = '20250723_1130_l'  
TracerMass =  72.46
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 13.30
m_calib_solution2 = 10.39
m_calib_solution3 = 10.54
m_calib_solution4 = NULL            


# 23 July 12:40 ----------------------------------------------------------------------
# L side 
sheet_name = '20250723_1240_l'  
TracerMass =  81.17
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 13.41
m_calib_solution2 = 15.20
m_calib_solution3 = 10.60
m_calib_solution4 = NULL            

# # 23 July 13:20 ----------------------------------------------------------------------
# # R side 
# # Adjust this for each individual measurement
# sheet_name = '20250723_1320_r_BAD'  
# TracerMass =  59.20
# # CALIBRATION VIALS
# # This is from you field notebook
# m_calib_solution1 = 14.59
# m_calib_solution2 = 13.54
# m_calib_solution3 = 11.15
# m_calib_solution4 = NULL            


# 23 July 14:20 ----------------------------------------------------------------------
# L side 
sheet_name = '20250723_1420_l'  
TracerMass =  98.98
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 9.25
m_calib_solution2 = 12.64
m_calib_solution3 = 13.19
m_calib_solution4 = NULL    

# 23 July 15:17 ----------------------------------------------------------------------
# R side 
sheet_name = '20250723_1517_r'  
TracerMass =  153.04
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 13.73
m_calib_solution2 = 9.17
m_calib_solution3 = 11.65
m_calib_solution4 = NULL    


# 23 July 16:23 ----------------------------------------------------------------------
# L side 
sheet_name = '20250723_1623_l'  
TracerMass =  143.88
# CALIBRATION VIALS
# This is from you field notebook
m_calib_solution1 = 11.47
m_calib_solution2 = 13.83
m_calib_solution3 = 12.63
m_calib_solution4 = NULL    



# -------- Calibration preparation --------
# Needs to be filled in only once - from your Excel sheet "2025 Abramov - Lab preparation 10 ml (EN) v 2025-07-15.xlsx"
# This is the result from the dilution series.

rho1 = 1056     # g/l - density of the standard (adjust)
VCDS1 = 1       # liter - mixing flask volume for first dilution
SVDS1 = 40.23   # g - mass of sample from base solution in gramm
CDS1 = Standard * (SVDS1 / rho1) / VCDS1 # g/l - concentration of dilution series at step 1

# DILUTION STEP 2:
rho2 = 1000     # g/l - not measured, might in reality be higher than 1kg/l
VCDS2 = 1       # liter - mixing flask volume for second dilution
SVDS2 = 21.52   # mass of sample from Dilution Step1 solution in grams
CDS2 = CDS1 * (SVDS2 / rho2) / VCDS2    # g/l - concentration after dilution step2

# DILUTION STEP 3:
rho3 = 1000     # g/l - not measured, might in reality be higher than 1kg/l
VCDS3 = 1       # liter - mixing flask volume for second dilution
SVDS3 = 18.56   # g - mass of sample from Dilution Step2 solution in grams
CDS3 = CDS2 * (SVDS3 / rho3) / VCDS3    # g/l - concentration after dilution step3

calib_concentration = CDS3

# ------------ NO NEED TO CHANGE ANYTHING HEREAFTER --------------- #
# calibration masses in µg
cs1 = cs2 = cs3= cs4 = NULL
if(length(m_calib_solution1) != 0){
  cs1 = m_calib_solution1 *calib_concentration /1000 # /1000=to Liter assuming density of 1g/cm3; and to g of actual tracer mass by multiplying with DS2 concentration
} 
if(length(m_calib_solution2) != 0){
  cs2 = m_calib_solution2*calib_concentration /1000 
} 
if(length(m_calib_solution3) != 0){
  cs3 = m_calib_solution3*calib_concentration /1000 
} 
if(length(m_calib_solution4) != 0){
  cs4 = m_calib_solution4 *calib_concentration/1000 
} 
# Injected Tracer mass:
M = Standard * TracerMass / rho1 * 1000  # mg

# gc() # This cleans the memory - against JAVA Problems ...
setwd(path)
# source('../R/FUN_install_packages.R')
# Source all functions for cleaning and preparation
source('../0_R-FUN/FUN_curve-processing.R')


# ------- READ DATA ------- #
d_ = read_xlsx_(filename = filename_excel,sheet = sheet_name)
# ---- remove NAs 
d_ = rm_nas(d_)

par(mar=c(4,4,.2,4))
plot(d_$X1, d_$X4, type='l')
par(new=T)
plot(d_$X1, d_$X7, type='l', axes=F, ann=F, col='red')# temperature plot
axis(4)
mtext('Temperature [ºC]', side=4, line=2.6, col='red')


d_ = na.omit(d_)
# ---- Make date-time
tmp_date = make_date_time(d_)

# remove FL30-determined baseline signal ?
Tracer1=d_$X4 - d_$X6
# ---- Combine data
d = data.frame(date=tmp_date, Tracer1=Tracer1) # 2025-07-06 changed: Tracer1=d_$X4)

# ---- Noise removal
d = remove_noise(d)

# ---- Calibration
calibrate(d, start = 1,stop =  900,cs1 = cs1, cs2 = cs2, cs3 = cs3,bucketvolume = 5)  # values are first and last point (n); adjust if you cannot see the calibration

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
calc_discharge(d,start = 1000)


# ---- Curve 2 
# If second (overlapping) breakthrough curve exists:
print("Is there a second breakthrough curve (with overlap)?")

# # Was the same amount of tracer used? --> Change if yes!
# # ----- Change the following two Arguments if need be ---------------------------- #
# Standard = Standard          # g/l - The concentration of the color tracer (Standard solution)
# TracerVolume = TracerVolume  # l - How many liters! were injected into the river?
# # -------------------------------------------------------------------------------- #
# M = Standard * TracerVolume * 1000 
# 
# # calc_discharge_overlap(d, dss)
# 

