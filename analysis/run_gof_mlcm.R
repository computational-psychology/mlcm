## Analysis of MLCM data - scaling on White's stimulus
## Goodness of fit analysis

## script calls the same functions used to analyse simulated data
setwd("~/git/white_scaling/analysis")

observers <- list('dk', 'ga6', 'jxv2', 'lxs', 'mm', 'pe', 'aa', 'js', 'xz')

source('../simulation_mlcm/gof_mlcm.R')

for (obsname in observers){
  print('*******************************************')
  print(obsname)
  rootname = paste('../data/parsed_results/', obsname, '_reindexed', sep = '')
  
  #print('********** all data *****************')
  gof_mlcm(rootname, modeltype="add")
  gof_mlcm(rootname, modeltype="full")
  
  # GoF for dataset with outliers sequentially removed is done in main script: analysis_mlcm.R
  #print('********** outliers removed *****************')
  #gof_mlcm(rootname, modeltype="add", fr=TRUE)
  #gof_mlcm(rootname, modeltype="full", fr=TRUE) 
  
  print('*******************************************')
  
}


# EOF
