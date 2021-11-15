#### MLCM analysis
comparemodels <- function(rootname) {
  
#rootname <- 'sim_mlcm'

library('MLCM')

modeltype <- 'add'
load(paste(rootname, '_', modeltype, '.glm.MLCM', sep = ""))

obs.add <- obs


modeltype <- 'full'
load(paste(rootname, '_', modeltype, '.glm.MLCM', sep = ""))

obs.full <- obs

print(anova(obs.add, obs.full, test='Chisq'))
  
}

# EOF
