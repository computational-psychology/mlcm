#### MLCM analysis
gof_mlcm <- function(rootname, modeltype="full", fr=FALSE) {

#rootname <- 'sim_mlcm'
#modeltype <- "add"

library(MLCM)
library(snow)
ncores <- 4
workers <- replicate(ncores, "localhost")
master <- "localhost"

source('gofutils.R')
source("pbinom.diagnostics.mlcm.R")

# epsilon is the resolution given to the optimization routine. At a difference
# of epsilon is where the algorithm stops. We have issues with the default
# epsilon for the full model. It tends to be stuck at local minima 
# and overestimates the scale values. This happens particularly bad for the
# bootstrap samples. I manually and by hand decresed the epsilon value
# to a value that does not give those results. It's a hack but it seems
# to work. Alternatively one would have to try another optimization algorithm
# more robust to local minima. G.A. 
# # default is epsilon = 1e-14. 
epsilon <- 1e-4  

print(paste('running: GoF MLCM ', rootname, sep=''))

rootname = paste(rootname, '_', modeltype, sep = "")


suffix <- '.glm.MLCM'
suffixsave <- '.glm.diags.MLCM'

if(fr){
   suffix <- paste('.fr', suffix, sep="")
   suffixsave <- paste('.fr', suffixsave, sep="")
}

file2read <- paste(rootname, suffix, sep = "")
file2save <- paste(rootname, suffixsave, sep = "")

print(paste('reading ', file2read, sep=""))
print(paste('saving in  ', file2save, sep=""))

load(file2read)


obs.diags <- pbinom.diagnostics(obs, nsim=1000, workers=workers, master=master,
                                 control=glm.control(epsilon=epsilon))
   
plot(obs.diags)


# print the statistics
per <- evaluateResiduals(obs.diags)
p <- obs.diags$p
print(paste('Percentage inside envelope CDF deviance residuals: ', per, sep=""))
print(paste('P-value of number of runs histogram: ', p, sep=""))


save(obs.diags, per, p, file=file2save)

print('Done')


}


# EOF
