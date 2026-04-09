# - reading FL30 raw data
# - transforming data into readable format with signal in mV

# Arguments
path = "/Users/pohle/Dropbox/Central_Asia/Fluorometer/data/KG_G354/"
path = "~/work/mountain-hydrology-workshop-2026/Fluorometer/KG_G354"

setwd(path)
# For Windows it will be something like this:
# path = "C:/summer_school_Suyek/data/"

# Input files
filename_raw = '2019 - 1664.txt'
# Output files
filename_mV = '2019 - f1664.mv'


# Input files
filename_raw = '2021 - f1664.txt'
# Output files
filename_mV = '2021 - f1664.mv'

# Input files
filename_raw = '2022 - f1664.txt'
# Output files
filename_mV = '2022 - f1664.mv'
# Input files


# Input files
filename_raw = '2023 - f1664.txt'
# Output files
filename_mV = '2023 - f1664.mv'

# Input files
filename_raw = '2024 - f1664.txt'
# Output files
filename_mV = '2024 - f1664.mv'



# ------------ NO NEED TO CHANGE ANYTHING HEREAFTER --------------- #
# source('../0_R-FUN//FUN_install_packages.R')
source("../0_R-FUN/FUN_binary_to_mv.R")

aaa = bit_to_mv(data_file = paste0(path, filename_raw))
tail(aaa)
head(aaa)
opar <- par()
par(mfrow=c(2,1), mar=c(4,4,.2,.2))
plot(aaa$Tracer1, type='l', xlab='Time [s]', ylab='Signal [mV]')

plot(aaa$date,aaa$Tracer1, type='l', xlab='Date', ylab='Signal [mV]')
par(opar)

write.table(aaa,file = paste0(path,filename_mV),
            quote = F, row.names = F)
