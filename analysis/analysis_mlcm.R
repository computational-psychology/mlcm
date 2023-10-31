# Functions to estimate perceptual scales with MLCM
library(MLCM)
library(snow)

# TODOS
# separate estimate_scales into smaller functions
# add normalization of scales to 1, with corresponding CI calculation (done in python before)
# save everything as CSVs - raw and normalized scales - bootstrap samples as well

################################################################################
##################### Function definitions #####################################
################################################################################

#' Parallelized version of 'boot.mlcm':  Resampling of an Estimated Conjoint Measurement Scale
#' Same implementation as boot.mlcm but adapted to run in parallel
#' on different hosts (processes in the same machine or different machines)
#' using the package 'snow'.
#'
#' Same parameters as boot.mlcm, with the addition of
#' @param ncores number of cores. Default 1.
#'
pboot.mlcm <- function(x, nsim, ncores=1, ...){
  
  workers <- replicate(ncores, "localhost")

  # working with snow
  cl <- makeSOCKcluster(names=workers)

  d <- as.matrix(x$obj$data[, -1])
  p <- fitted(x)
  rsim <- matrix(rbinom(length(p) * nsim, 1, p), 
                 nrow = length(p), ncol = nsim)
  
  clusterExport(cl, c("rsim", "d", "x"), envir= environment() )
  
  bts.samp <- parApply(cl, rsim, 2, function(y, dd) {
    psct <- glm.fit(dd, y, family = binomial(x$link), ...)$coefficients
    names(psct) <- x$stimulus[-1]
    psct
  }, dd = d)
  
  stopCluster(cl)
  
  
  list(boot.samp = bts.samp, 
       bt.mean = apply(bts.samp, 1, mean), 
       bt.sd = apply(bts.samp, 1, sd), N = nsim)
}



#' Calculates the percentage of residuals falling inside the 95 % envelope obtained
#' via bootstrap. A higher percentage indicates that the observed residuals are 
#' distributed in a similar fashion as simulated data generated with the observer
#' model assumed by MLDS/MLCM. In other words, a higher percentage indicates 
#' better goodness of fit.
#'
#' @param x a goodness of fit diagnostics object (from MLDS or MLCM)
#'
#' @return the percentage  inside the envelope (numeric)
#'
#' @examples
#' obs <- mlcm(data)
#' obs.diags <- binom.diagnostics(obs)
#' percentage_residuals_in_envelope(obs.diags)
percentage_residuals_in_envelope <- function(x){
  
  nsim <- dim(x$resid)[1]
  n <- dim(x$resid)[2]
  alpha = 0.025
  
  splUpper <- smooth.spline(x$resid[alpha*nsim,], (1:n-0.5)/n)
  splLower <- smooth.spline(x$resid[(1-alpha)*nsim,], (1:n-0.5)/n)
  splObs <- smooth.spline(sort(x$Obs.resid), (1:n-0.5)/n)
  
  nfit <- 0
  for(i in (1:length(splObs$x))){
    xval <- (splObs$x)[i]
    if( (predict(splObs, xval)$y < predict(splUpper, xval)$y) && (predict(splObs, xval)$y > predict(splLower, xval)$y) ){
      nfit <- nfit +1
    }
  }
  percentage <- (nfit*100)/length(splObs$x)
  return(percentage)
}



#' Parallelized version of 'binom.diagnostics': Diagnostics for Binary GLM
#' Same implementation as binom.diagnostics but adapted to run in parallel
#' on different hosts (processes in the same machine or different machines)
#' using the package 'snow'.
#'
#' Same parameters as boot.mlcm, with the addition of
#' @param ncores number of cores. Default 1.
pbinom.diagnostics <- function(obj, nsim = 200, type = "deviance", no.warn = TRUE, ncores=1, ...) 
{
  
  workers <- replicate(ncores, "localhost")

  # working with snow
  # initialize cluster
  cl <- makeSOCKcluster(names=workers)
  
  # loads MLCM package on each of the workers
  clusterEvalQ(cl, library(MLCM))
  
  if (no.warn){
    old.opt <- options(warn = -1)
    on.exit(options(old.opt))
  }
  
  n <- length(fitted(obj))
  d <- obj$obj$data[, -1]
  ys <- matrix(rbinom(n * nsim, 1, fitted(obj)), 
               ncol = nsim)
  
  # export needed variables to each worker 
  clusterExport(cl, c("obj", "n", "d", "type", "ys"), envir= environment() )
  
  res <- parSapply(cl, seq_len(nsim), function(x, obj){
    #		ys <- rbinom(n, 1, fitted(obj))
    d2 <- cbind(resp = ys[, x], d)
    lnk <- obj$obj$family$link
    br <- glm(resp ~ . - 1, binomial(link = lnk), d2, ...)
    rs <- residuals(br, type = type)
    rsd <- sort(rs)
    fv.sort <- sort(fitted(br), index.return = TRUE)
    rs <- rs[fv.sort$ix]
    rs <- rs > 0
    runs <- sum(rs[1:(n-1)] != rs[2:n])
    list(resid = as.vector(rsd), NumRuns = runs)
  }, obj = obj
  ) 
  
  # after all done, stops cluster
  stopCluster(cl)
  
  fres <- list(NumRuns = sapply(seq(2, length(res), 2), 
                                function(x) res[[x]]))
  fres$resid <- t(do.call("cbind", 
                          list(sapply(seq(1, length(res), 2), 
                                      function(x) res[[x]]))))
  fres$resid <- apply(fres$resid, 2, sort)
  fres$Obs.resid <- residuals(obj$obj, type = type)
  rs <- residuals(obj$obj, type = type)
  fv.sort <- sort(fitted(obj), index.return = TRUE)
  rs <- rs[fv.sort$ix]
  rs <- rs > 0
  obs.runs <- sum(rs[1:(n-1)] != rs[2:n])
  nr <- sum(fres$NumRuns > obs.runs) 
  fres$ObsRuns <- obs.runs
  fres$p <- 1 - nr/nsim
  class(fres) <- c("mlcm.diag", "list")
  fres
}


estimate_scales <- function(rootname, 
                            modeltype="full", 
                            do_bootstrap=FALSE, 
                            nsim=1000, 
                            fr=FALSE, 
                            thr='auto') {
  
  ncores <- 4

  cat('********** Estimating scales - START **********\n')
  # epsilon is the resolution given to the optimization routine. At a difference
  # of epsilon is where the algorithm stops. We have issues with the default
  # epsilon for the full model. It tends to be stuck at local minima 
  # and overestimates the scale values. This happens particularly bad for the
  # bootstrap samples. I manually and by hand decreased the epsilon value
  # to a value that does not give those results. It's a hack but it seems
  # to work. Alternatively one would have to try another optimization algorithm
  # more robust to local minima. GA. 
  # # default is epsilon = 1e-8. 
  epsilon <- 1e-4 
  
  df <- read.csv(paste(rootname, '.csv', sep = ""), sep = ',')
  keeps <- c("Resp", "L1", "L2", "C1", "C2")
  df1 <- df[keeps]
  cat(paste('number of observations:', nrow(df1), sep=' '))
  
  
  ### estimating the scales
  obs <- mlcm(df1, model = modeltype, method='glm.fit', lnk='probit', control=glm.control(epsilon=epsilon))
  print(obs)
  
  #plot(obs, type='b')
  
  # refiting by filtering trials with high residuals. take the high residuals of the full model
  if (fr) {
    
    # if we're calculating the additive model, we get the outliers from the residuals of the full model. 
    # thus we need to quicky fit the full model first....
    if (modeltype == 'add'){
      obs <- mlcm(df1, model = 'full', method='glm.fit', lnk='probit', control=glm.control(epsilon=epsilon))
    }
    
    if (is.numeric(thr)){
      
      cat('*** removing trials with residuals higher than a threshold to improve goodnesss of fit ***\n')
      
      # thr is arbitrary, thr = 2.5 in the book and in our previous work
      y <- df1[((residuals(obs$obj) > -thr) & (residuals(obs$obj) < thr)), ]
      cat(paste('dataset reduced to -> ', nrow(y), '\n', sep=""))
      
      obs <- mlcm(y, model = modeltype, method='glm.fit', lnk='probit', control=glm.control(epsilon=epsilon))
      
    } else{
      # we get the vector of residuals (deviance residual)
      res <- residuals(obs$obj)
      s <- sort(abs(res), decreasing=TRUE, index.return=TRUE) # return sorted value AND index
      
      # first 10 indices with highest deviance residuals 
      #res[s$ix[1:10]]
      
      finished <- FALSE
      start <- 1
      while(!finished){
        
        cat('*** iteratively removing putative outliers (trials with high residuals) to improve goodnesss of fit ***\n')
        
        # select first trials
        y <- df1[sort(s$ix[start:nrow(df1)]), ]
        
        removed <- df1[s$ix[1:start-1],]
        write.csv(removed, paste(rootname, '_removed.csv', sep = ""))
        
        cat(paste('dataset reduced to -> ', nrow(y), '\n', sep=""))
        cat(paste('removed -> ', nrow(removed), '\n', sep=""))
        
        obs <- mlcm(y, model = modeltype, method='glm.fit', lnk='probit', control=glm.control(epsilon=epsilon))
        
        # evaluate GoF
        obs.diags <- pbinom.diagnostics(obs, nsim=1000, ncores=ncores,
                                        control=glm.control(epsilon=1e-4))
        
        #plot(obs.diags)
        
        
        # print the statistics
        per <- percentage_residuals_in_envelope(obs.diags)
        p <- obs.diags$p
        cat(paste('Percentage inside envelope CDF deviance residuals: ', per, '\n', sep=""))
        cat(paste('p-value of number of runs histogram: ', p, '\n',sep=""))
        #cat(obs.diags$ObsRuns)
        
        # if p-val <0.05 then take one trial less (start +=1)
        if (p<0.05){
          cat('eliminating one trial more... \n\n')
          start <- start +1
        } else{ # if p-val >=0.05, break out of loop
          cat('p-value >= 0.05, breaking the loop \n\n')
          finished <- TRUE
        }
        
        # saving GOF data in diags.MLCM
        rootname2 = paste(rootname, '_', modeltype, sep = "")
        suffixsave <- '.fr.glm.diags.MLCM'
        file2save <- paste(rootname2, suffixsave, sep = "")
        save(obs.diags, per, p, file=file2save)
        
      }
      
    }
    suffix <- '.fr.glm.MLCM'
  } 
  else{
    suffix <- '.glm.MLCM'
  }
  
  
  # scale values are:
  obs.scales <- obs$pscale
  
  if (modeltype=='add'){
    
    additiveshift <- obs$obj$coefficients[length(obs$obj$coefficients)]
    obs.scales[,2] <- obs.scales[,1] + additiveshift
  }
  
  
  if(do_bootstrap){
    ### calculating confidence intervals
    cat('bootstrapping the model to calculate confidence intervals\n')
    
    # we first bootstrap the model
    obs.boot <- pboot.mlcm(obs, nsim=nsim, ncores=ncores, control=glm.control(epsilon=epsilon))
    
    ## here  we manually calculate the percentile confidence intervals from the bootstrap samples
    # with 95 % confidence
    samples <- obs.boot$boot.samp
    
    # getting number of contexts
    nc <- as.integer(ncol(obs$pscale))
    
    
    ## if the model is additive, we need to rearrange the bootstrap samples a bit
    ## to get the full matrix
    if (modeltype=='add'){
      additiveshift <- samples[nrow(samples),]
      
      context1 <- samples[1:nrow(samples)-1,]
      
      context2 <- rbind(rep(0, nsim), samples[1:nrow(samples)-1,]) + additiveshift
      
      samples <- rbind(context1, context2)
      
    }
    
    
    # samples a matrix of size n params x n boostrap samples
    # we then calculate for each row (each parameter) the percentiles
    
    obs.low <- c(0, apply(samples, 1, quantile, probs = 0.025))
    obs.high <- c(0, apply(samples, 1, quantile, probs = 0.975))
    
    # reformat to a matrix
    dim(obs.low) <- c(length(obs.low)/nc, nc)
    dim(obs.high) <- c(length(obs.high)/nc, nc)
    
    
    # the confidence intervals for each scale estimate are
    # lower bound:
    #print(bg.low)
    
    # upper bound:
    #print(bg.high)
    
    save(obs, obs.boot, obs.scales, obs.low, obs.high, samples, file=paste(rootname, '_', modeltype, suffix, sep = ""))
    print(paste('saving in..', rootname, '_', modeltype, suffix, sep = ""))
    
  }else{
    save(obs, obs.scales, file=paste(rootname, '_', modeltype, suffix, sep = ""))
    
  }
  
  
  cat('********** Estimating scales - END **********\n')
  cat('*********************************************\n')
  return(obs)

}





################################################################################
##################### Analysis of a particular dataset #########################
################################################################################


filename = '/home/guille/git/surround_brightness/surround_brightness/data/example_processed_data'

# estimates scales with additive model
obs.add <- estimate_scales(filename, 'add')

# estimate scales with full ('saturated') model
obs.full <- estimate_scales(filename, 'full')

# compares which models explains the data better
cat('********** Comparing ADD vs FULL model **********\n')
print(anova(obs.add, obs.full, test='Chisq'))

###
estimate_scales(filename, 'full', 
                do_bootstrap=TRUE , 
                nsim=1000, 
                fr=TRUE,
                thr='auto')


