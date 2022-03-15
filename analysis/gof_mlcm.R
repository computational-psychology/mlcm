## Analysis of MLCM data - scaling on White's stimulus
## Goodness of fit analysis

## script calls the same functions used to analyse simulated data
setwd("~/git/white_scaling/analysis")

# variables
observers <- list('ga', 'ga2', 'jxv', 'ga3', 'ga4','ga5','dk','ga6','jxv2','lxs', 'mm')
#observers <- list('mm')

source('../simulation_mlcm/gof_mlcm.R')


for (obsname in observers){
  print('*******************************************')
  print(obsname)
  rootname = paste('../data/parsed_results/', obsname, '_reindexed', sep = '')
  
  print('********** all data *****************')
  gof_mlcm(rootname, modeltype="add")
  gof_mlcm(rootname, modeltype="full")
  
  print('********** outliers removed *****************')
  gof_mlcm(rootname, modeltype="add", fr=TRUE)
  gof_mlcm(rootname, modeltype="full", fr=TRUE) 
  
  print('*******************************************')
  
}


# EOF
