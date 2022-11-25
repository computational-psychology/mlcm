## Analysis of MLCM data - scaling on White's stimulus
## script calls the same functions used to analyse simulated data

setwd("~/git/white_scaling/analysis")
# options(warn=1)

#observers <- list('dk','ga6','jxv2','lxs', 'mm')
thr <- 'auto'
#observers <- list('aa')
#thr <- 2.15
observers <- list('js')

calculateCI = TRUE  # if true, calculated CI using bootstrap. it takes some time

source('../simulation_mlcm/analysis_mlcm.R')
source('../simulation_mlcm/comparemodels.R')

nsim = 1000

for (obsname in observers){
   print('*******************************************')
   print(obsname)
   print('********** all data *****************')
   rootname = paste('../data/parsed_results/', obsname, '_reindexed', sep = '')
   analyzemlcm(rootname, 'add', do_bootstrap=calculateCI , nsim=nsim, fr=FALSE)
   analyzemlcm(rootname, 'full', do_bootstrap=calculateCI , nsim=nsim, fr=FALSE)
   comparemodels(rootname)
   
   print('******* finding outliers and removing according to GoF *************')
   analyzemlcm(rootname, 'full', do_bootstrap=calculateCI , nsim=nsim, fr=TRUE, thr=thr)
   
   
   print('*******************************************')
   
}


# EOF

