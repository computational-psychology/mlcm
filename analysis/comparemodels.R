#### MLCM analysis
comparemodels <- function(rootname,fr=FALSE) {
  
#rootname <- 'sim_mlcm'

library('MLCM')

if(fr){
  suffix <- '.fr.glm.MLCM'
} 
else{
  suffix <- '.glm.MLCM'
}


modeltype <- 'add'
load(paste(rootname, '_', modeltype, suffix, sep = ""))

obs.add <- obs


modeltype <- 'full'
load(paste(rootname, '_', modeltype, suffix, sep = ""))

obs.full <- obs

print(anova(obs.add, obs.full, test='Chisq'))
  
}

# EOF
