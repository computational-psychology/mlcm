## Analysis of MLCM data - scaling on White's stimulus
## script calls the same functions used to analyse simulated data

setwd("~/git/white_scaling/experiment/analysis")
# options(warn=1)

#observers <- list('ga', 'ga2', 'jxv', 'ga3', 'ga4','ga5','dk','ga6','jxv2','lxs')
#observers <- list('ga', 'ga2', 'jxv', 'ga3', 'ga4','ga5')
observers <- list('mm')

calculateCI = TRUE  # if true, calculated CI using bootstrap. it takes some time

source('../../simulation_mlcm/analysis_mlcm.R')
source('../../simulation_mlcm/comparemodels.R')

nsim = 10000

for (obsname in observers){
   print('*******************************************')
   print(obsname)
   print('********** all data *****************')
   rootname = paste('parsed_results/', obsname, '_reindexed', sep = '')
   analyzemlcm(rootname, 'add', do_bootstrap=calculateCI , nsim=nsim)
   analyzemlcm(rootname, 'full', do_bootstrap=calculateCI , nsim=nsim)
   
   comparemodels(rootname)
   
   print('********** removing some outliers *****************')
   analyzemlcm(rootname, 'add', do_bootstrap=calculateCI , nsim=nsim, fr=TRUE)
   analyzemlcm(rootname, 'full', do_bootstrap=calculateCI , nsim=nsim, fr=TRUE)
   
   comparemodels(rootname)
   
   
   print('*******************************************')
   
}


# EOF

