#### Functions and analysis pipeline for MLCM data - surround brightness project
##
## It gets as input a CSV filename where data from an MLCM experiment is located.
## The format should comply with the standard format for MLCM (see example)
## Outputs are the estimate scales as CSV files. It also saves the bootstrap
## samples used for the CI estimation, and the raw R objects as a .rds file.
##
## Limitations:
## - the stimulus dimensions are hard coded (luminance and context)
## - it allows only 2 contexts (for ex. in white and in black, for White's).
##   code would need to be refactored further to make it more general.
##
## author: G. Aguilar, Nov 2023

library(MLCM)
library(snow)

##################### Function definitions #####################################

#' Parallelized version of 'boot.mlcm':  Resampling of an Estimated Conjoint Measurement Scale
#' Same implementation as boot.mlcm but adapted to run in parallel
#' on different hosts (processes in the same machine, or even in different machines)
#' using the package 'snow'.
#'
#' Same parameters as boot.mlcm, with the addition of
#' @param ncores number of cores. Default 1.
#'
pboot.mlcm <- function(x, nsim, ncores = 1, ...) {
  workers <- replicate(ncores, "localhost")

  # working with snow
  cl <- makeSOCKcluster(names = workers)

  d <- as.matrix(x$obj$data[, -1])
  p <- fitted(x)
  rsim <- matrix(rbinom(length(p) * nsim, 1, p),
    nrow = length(p), ncol = nsim
  )

  clusterExport(cl, c("rsim", "d", "x"), envir = environment())

  bts.samp <- parApply(cl, rsim, 2, function(y, dd) {
    psct <- glm.fit(dd, y, family = binomial(x$link), ...)$coefficients
    names(psct) <- x$stimulus[-1]
    psct
  }, dd = d)

  stopCluster(cl)


  list(
    boot.samp = bts.samp,
    bt.mean = apply(bts.samp, 1, mean),
    bt.sd = apply(bts.samp, 1, sd), N = nsim
  )
}



#' Parallelized version of 'binom.diagnostics': Diagnostics for Binary GLM
#' Same implementation as binom.diagnostics but adapted to run in parallel
#' on different hosts (processes in the same machine, or even on different machines)
#' using the package 'snow'.
#'
#' Same parameters as boot.mlcm, with the addition of
#' @param ncores number of cores. Default 1.
pbinom.diagnostics <- function(obj, nsim = 200, type = "deviance", no.warn = TRUE, ncores = 1, ...) {
  workers <- replicate(ncores, "localhost")

  # working with snow
  # initialize cluster
  cl <- makeSOCKcluster(names = workers)

  # loads MLCM package on each of the workers
  clusterEvalQ(cl, library(MLCM))

  if (no.warn) {
    old.opt <- options(warn = -1)
    on.exit(options(old.opt))
  }

  n <- length(fitted(obj))
  d <- obj$obj$data[, -1]
  ys <- matrix(rbinom(n * nsim, 1, fitted(obj)),
    ncol = nsim
  )

  # export needed variables to each worker
  clusterExport(cl, c("obj", "n", "d", "type", "ys"), envir = environment())

  res <- parSapply(cl, seq_len(nsim), function(x, obj) {
    # 		ys <- rbinom(n, 1, fitted(obj))
    d2 <- cbind(resp = ys[, x], d)
    lnk <- obj$obj$family$link
    br <- glm(resp ~ . - 1, binomial(link = lnk), d2, ...)
    rs <- residuals(br, type = type)
    rsd <- sort(rs)
    fv.sort <- sort(fitted(br), index.return = TRUE)
    rs <- rs[fv.sort$ix]
    rs <- rs > 0
    runs <- sum(rs[1:(n - 1)] != rs[2:n])
    list(resid = as.vector(rsd), NumRuns = runs)
  }, obj = obj)

  # after all done, stops cluster
  stopCluster(cl)

  fres <- list(NumRuns = sapply(
    seq(2, length(res), 2),
    function(x) res[[x]]
  ))
  fres$resid <- t(do.call(
    "cbind",
    list(sapply(
      seq(1, length(res), 2),
      function(x) res[[x]]
    ))
  ))
  fres$resid <- apply(fres$resid, 2, sort)
  fres$Obs.resid <- residuals(obj$obj, type = type)
  rs <- residuals(obj$obj, type = type)
  fv.sort <- sort(fitted(obj), index.return = TRUE)
  rs <- rs[fv.sort$ix]
  rs <- rs > 0
  obs.runs <- sum(rs[1:(n - 1)] != rs[2:n])
  nr <- sum(fres$NumRuns > obs.runs)
  fres$ObsRuns <- obs.runs
  fres$p <- 1 - nr / nsim
  class(fres) <- c("mlcm.diag", "list")
  fres
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
percentage_residuals_in_envelope <- function(x) {
  nsim <- dim(x$resid)[1]
  n <- dim(x$resid)[2]
  alpha <- 0.025

  splUpper <- smooth.spline(x$resid[alpha * nsim, ], (1:n - 0.5) / n)
  splLower <- smooth.spline(x$resid[(1 - alpha) * nsim, ], (1:n - 0.5) / n)
  splObs <- smooth.spline(sort(x$Obs.resid), (1:n - 0.5) / n)

  nfit <- 0
  for (i in (1:length(splObs$x))) {
    xval <- (splObs$x)[i]
    if ((predict(splObs, xval)$y < predict(splUpper, xval)$y) && (predict(splObs, xval)$y > predict(splLower, xval)$y)) {
      nfit <- nfit + 1
    }
  }
  percentage <- (nfit * 100) / length(splObs$x)
  return(percentage)
}




pivot_table_scales <- function(obs.scales) {
  obs.long <- reshape(obs.scales,
    varying = c("Context.1", "Context.2"),
    timevar = "context", v.names = "scale", direction = "long"
  )
  obs.long <- subset(obs.long, select = -id) # removing id column

  return(obs.long)
}


#' Estimate perceptual scales from data using MLCM
#'
#' @param filename path to CSV file in the expected format (see example-data.csv)
#' @param modeltype 'add' or 'full', for the type of model to be tested
#' @param do_bootstrap TRUE or FALSE, whether to calculate bootstrap confidence
#'                    intervals or not. Default: FALSE
#' @param nsim number of bootstrap samples. Default=1000
#' @param remove_outliers TRUE or FALSE, whether or not to run goodness of fit
#'                        analyses and sequentially remove the trials with highest
#'                        residuals (putative outliers) until a "good" GoF. Default: FALSE
#' @param plotflag TRUE or FALSE, whether to do plots or not.
#' @param normalized TRUE or FALSE. TRUE if resulting scales should be normalized
#'                    to its maximum. Default: FALSE
#' @param savecsv TRUE or FALSE, whether to save scales as CSV files.
#'                Default: FALSE. If you want to save the scales for further analysis
#'                then it needs to be set to TRUE.
#' @param saverds TRUE or FALSE, whether to save raw R objects in a Rds file.
#'                Default: FALSE. It is good practice to switch to TRUE
#'                for the final analysis, for archiving purposes.
#'
#' @return None. Output scales are saved as CSV files.
#'
estimate_scales <- function(filename,
                            modeltype = "full",
                            do_bootstrap = FALSE,
                            nsim = 1000,
                            remove_outliers = FALSE,
                            plotflag = FALSE,
                            normalized = FALSE,
                            savecsv = FALSE,
                            saverds = FALSE) {
  ncores <- 4

  cat("********** Estimating scales - START **********\n")
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

  name <- basename(filename)
  rootname <- strsplit(name, ".csv")[[1]]
  dname <- dirname(filename)

  df <- read.csv(filename, sep = ",")
  keeps <- c("Resp", "L1", "L2", "C1", "C2")
  df1 <- df[keeps]
  cat(paste("number of trials:", nrow(df1), sep = " "))


  ### estimating the scales
  obs <- mlcm(df1, model = modeltype, method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))
  print(obs)

  if (plotflag) {
    plot(obs, type = "b")
  }

  # refitting by filtering trials with high residuals. take the high residuals of the full model
  if (remove_outliers) {
    # if we're calculating the additive model, we get the outliers from the residuals of the full model.
    # thus we need to quicky fit the full model first....
    if (modeltype == "add") {
      obs <- mlcm(df1, model = "full", method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))
    }


    # we get the vector of residuals (deviance residual)
    res <- residuals(obs$obj)
    s <- sort(abs(res), decreasing = TRUE, index.return = TRUE) # return sorted value AND index

    finished <- FALSE
    start <- 1
    while (!finished) {
      cat("***********************************************************************\n")
      cat("*** iteratively removing putative outliers (trials with high residuals)\n")
      cat("     to improve goodnesss of fit **************************************\n")

      # select first trials
      y <- df1[sort(s$ix[start:nrow(df1)]), ]

      removed <- df1[s$ix[1:start - 1], ]
      write.csv(removed, file.path(dname, paste(rootname, "-trialsremoved.csv", sep = "")))

      cat(paste("dataset reduced to -> ", nrow(y), " trials \n", sep = ""))
      cat(paste("removed -> ", nrow(removed), " trials \n", sep = ""))

      obs <- mlcm(y, model = modeltype, method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))

      # evaluate GoF
      obs.diags <- pbinom.diagnostics(obs,
        nsim = 1000, ncores = ncores,
        control = glm.control(epsilon = 1e-4)
      )
      if (plotflag) {
        plot(obs.diags)
      }


      # print the GoF statistics
      per <- percentage_residuals_in_envelope(obs.diags)
      p <- obs.diags$p
      cat("goodness of fit measures:\n")
      cat(paste("- percentage inside envelope CDF deviance residuals: ", per, "\n", sep = ""))
      cat(paste("- p-value of number of runs histogram: ", p, "\n", sep = ""))

      # if p-val <0.05 then take one trial less (start +=1)
      if (p < 0.05) {
        cat("...eliminating one more trial... \n\n")
        start <- start + 1
      } else { # if p-val >=0.05, break out of loop
        cat("...p-value >= 0.05, iteration finished.\n\n")
        finished <- TRUE
      }
    } # end while

    suffix <- "-or"
  } else { # end if(remove_outliers)
    suffix <- ""
  }

  # scale values, reformatting names of rows and columns
  obs.scales <- obs$pscale
  colnames(obs.scales) <- c("Context.1", "Context.2")
  for (i in 1:nrow(obs.scales)) {
    rownames(obs.scales)[i] <- i
  }


  #
  if (modeltype == "add") {
    additiveshift <- obs$obj$coefficients[length(obs$obj$coefficients)]
    obs.scales[, 2] <- obs.scales[, 1] + additiveshift
  }


  # we normalize the scale values
  if (normalized) {
    obs.scales <- obs.scales / obs.scales[nrow(obs.scales), 2]
    normsuffix <- "-norm"
  } else {
    normsuffix <- ""
  }


  # filenames where to save
  rdsfile2save <- file.path(dname, paste(rootname, "-", modeltype, suffix, ".Rds", sep = ""))
  scales2save <- file.path(dname, paste(rootname, "-", modeltype, normsuffix, suffix, "-scales.csv", sep = ""))
  bootscales2save <- file.path(dname, paste(rootname, "-", modeltype, normsuffix, suffix, "-bootsamples.csv", sep = ""))

  #
  if (do_bootstrap) {
    ### calculating confidence intervals
    cat("bootstrapping the model to calculate confidence intervals\n")

    # we first bootstrap the model
    obs.boot <- pboot.mlcm(obs, nsim = nsim, ncores = ncores, control = glm.control(epsilon = epsilon))
    # obs.boot <- boot.mlcm(obs, nsim=nsim, control=glm.control(epsilon=epsilon))

    ## here  we manually calculate the percentile confidence intervals from the bootstrap samples
    # with 95 % confidence
    samples <- obs.boot$boot.samp

    # getting number of contexts
    nc <- as.integer(ncol(obs$pscale))

    ## if the model is additive, we need to rearrange the bootstrap samples a bit
    ## to get the full matrix
    if (modeltype == "add") {
      additiveshift <- samples[nrow(samples), ]

      context1 <- samples[1:nrow(samples) - 1, ]
      context2 <- rbind(rep(0, nsim), samples[1:nrow(samples) - 1, ]) + additiveshift

      samples <- rbind(context1, context2)
    }

    # if we want normalized scales, we divide the samples matrix by the maximum
    # in each sample.
    if (normalized) {
      maximum <- samples[nrow(samples), ]
      samples <- t(t(samples) / maximum)
    }


    # samples a matrix of size n params x n boostrap samples
    # we then calculate for each row (each parameter) the percentiles
    obs.low <- c(0, apply(samples, 1, quantile, probs = 0.025))
    obs.high <- c(0, apply(samples, 1, quantile, probs = 0.975))

    # reformat to a matrix
    dim(obs.low) <- c(length(obs.low) / nc, nc)
    dim(obs.high) <- c(length(obs.high) / nc, nc)

    # the confidence intervals for each scale estimate are
    # lower bound:
    # print(obs.low)

    # upper bound:
    # print(obs.high)


    # save results in Rds file
    if (saverds && remove_outliers) {
      print(paste("saving in..", rdsfile2save, sep = ""))
      save(obs, obs.boot, obs.diags, per, p, file = rdsfile2save)
    } else if (saverds) {
      print(paste("saving in..", rdsfile2save, sep = ""))
      save(obs, obs.boot, file = rdsfile2save)
    }

    # save bootstrap samples in CSV file as well
    if (savecsv) {
      write.csv(t(samples), file = bootscales2save)
    }
  } # end if bootstrap
  else {
    # save results in Rds file
    if (saverds && remove_outliers) {
      print(paste("saving in..", rdsfile2save, sep = ""))
      save(obs, obs.diags, per, p, file = rdsfile2save)
    } else if (saverds) {
      print(paste("saving in..", rdsfile2save, sep = ""))
      save(obs, file = rdsfile2save)
    }
  }


  # save scales in CSV file
  # reformatting to long
  obs.scales <- data.frame(luminance = row.names(obs.scales), obs.scales)
  obs.scales <- pivot_table_scales(obs.scales)

  if (do_bootstrap) {
    # getting boundaries of confidence intervals also in the same format as scales
    obs.lowci <- data.frame(luminance = 1:nrow(obs.low), obs.low)
    colnames(obs.lowci) <- c("luminance", "Context.1", "Context.2")
    obs.lowci <- pivot_table_scales(obs.lowci)

    obs.highci <- data.frame(luminance = 1:nrow(obs.high), obs.high)
    colnames(obs.highci) <- c("luminance", "Context.1", "Context.2")
    obs.highci <- pivot_table_scales(obs.highci)

    # merging long scales dataframe with CI low and high boundaries
    tmp <- merge(obs.scales, obs.lowci, by = c("luminance", "context"), sort = FALSE)
    obs.scales <- merge(tmp, obs.highci, by = c("luminance", "context"), sort = FALSE)

    colnames(obs.scales) <- c("luminance", "context", "scale", "scale_CI_low", "scale_CI_high")
  }



  # saving as long-format CSV file
  if (savecsv) {
    write.csv(obs.scales, file = scales2save, row.names = FALSE)
  }

  cat("********** Estimating scales - END **********\n")
  cat("*********************************************\n")
  return(obs)
}
