# - reading FL30 raw data
# - transforming data into readable format with signal in mV

# Arguments
# path = "/Users/pohle/Dropbox/Central_Asia/Fluorometer/data/KG_G354/"
path = "~/work/mountain-hydrology-workshop-2026/Fluorometer/KG_G354/"

setwd(path)
# For Windows it will be something like this:
# path = "C:/Downloads/mountain-hydrology-workshop-2026/Fluorometer/KG_G354/"


# Input files
filename_raw = '2021 - f1664.txt'
# Output files
filename_mV = '2021 - f1664.mv'


# repeat for 2022, 2023, 2024, ...



# ------------ NO NEED TO CHANGE ANYTHING HEREAFTER --------------- #
source("../0_R-FUN/FUN_binary_to_mv.R")

data_in = bit_to_mv(data_file = paste0(path, filename_raw))
tail(data_in)
head(data_in)

plot(data_in$date,data_in$Tracer1, type='l', xlab='Date', ylab='Signal [mV]')

# write data (mV and normal CSV format)
write.table(aaa,file = paste0(path,filename_mV),quote = F, row.names = F)
