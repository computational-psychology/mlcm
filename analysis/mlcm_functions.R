#### Functions and analysis pipeline for MLCM data - surround brightness project
##
## It gets as input a CSV filename where data from an MLCM experiment is located.
## The format should comply with the standard format for MLCM (see example)
## Outputs are the estimate scales as CSV files. It also saves the bootstrap
## samples used for the CI estimation, and the raw R objects as a .rds file.
##
## Limitations:
## - the stimulus dimensions are hard coded (intensity and context)
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
pboot.mlcm <- function(x, nsim, ncores = 1, ...) { # nolint: object_name_linter.
  workers <- replicate(ncores, "localhost")

  # working with snow
  cl <- makeSOCKcluster(names = workers)

  d <- as.matrix(x$obj$data[, -1])
  p <- fitted(x)
  rsim <- matrix(rbinom(length(p) * nsim, 1, p),
    nrow = length(p), ncol = nsim
  )

  clusterExport(cl, c("rsim", "d", "x"), envir = environment())

  bts.samp <- parApply(cl, rsim, 2, function(y, dd) { # nolint: object_name_linter.
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
pbinom.diagnostics <- function( # nolint: object_name_linter.
    obj,
    nsim = 200,
    type = "deviance",
    warn = FALSE,
    ncores = 1, ...) {
  workers <- replicate(ncores, "localhost")

  # working with snow
  # initialize cluster
  cl <- makeSOCKcluster(names = workers)

  # loads MLCM package on each of the workers
  clusterEvalQ(cl, library(MLCM))

  if (!warn) {
    old_opt <- options(warn = -1)
    on.exit(options(old_opt))
  }

  n <- length(fitted(obj))
  d <- obj$obj$data[, -1]
  ys <- matrix(rbinom(n * nsim, 1, fitted(obj)),
    ncol = nsim
  )

  # export needed variables to each worker
  clusterExport(cl, c("obj", "n", "d", "type", "ys"), envir = environment())

  res <- parSapply(cl, seq_len(nsim), function(x, obj) {
    d2 <- cbind(resp = ys[, x], d)
    link <- obj$obj$family$link
    br <- glm(resp ~ . - 1, binomial(link = link), d2, ...)
    residuals <- residuals(br, type = type)
    residuals_sorted <- sort(residuals)
    fv_sorted <- sort(fitted(br), index.return = TRUE)
    residuals <- residuals[fv_sorted$ix]
    residuals <- residuals > 0
    runs <- sum(residuals[1:(n - 1)] != residuals[2:n])
    list(resid = as.vector(residuals_sorted), NumRuns = runs)
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
  fv_sorted <- sort(fitted(obj), index.return = TRUE)
  rs <- rs[fv_sorted$ix]
  rs <- rs > 0
  obs_runs <- sum(rs[1:(n - 1)] != rs[2:n])
  nr <- sum(fres$NumRuns > obs_runs)
  fres$ObsRuns <- obs_runs
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
perc_resid_in_envl <- function(x) {
  nsim <- dim(x$resid)[1]
  n <- dim(x$resid)[2]
  alpha <- 0.025

  spline_upper <- smooth.spline(x$resid[alpha * nsim, ], (1:n - 0.5) / n)
  spline_lower <- smooth.spline(x$resid[(1 - alpha) * nsim, ], (1:n - 0.5) / n)
  spline_obs <- smooth.spline(sort(x$Obs.resid), (1:n - 0.5) / n)

  nfit <- 0
  for (i in (1:length(spline_obs$x))) {
    xval <- (spline_obs$x)[i]
    if (
      (predict(spline_obs, xval)$y < predict(spline_upper, xval)$y) &&
        (predict(spline_obs, xval)$y > predict(spline_lower, xval)$y)
    ) {
      nfit <- nfit + 1
    }
  }
  percentage <- (nfit * 100) / length(spline_obs$x)
  return(percentage)
}


goodness_of_fit <- function(model, epsilon = 1e-4, ncores = 1, plots = FALSE) {
  model_diags <- pbinom.diagnostics(model,
    nsim = 1000, ncores = ncores,
    control = glm.control(epsilon = epsilon)
  )
  if (plots) {
    plot(model_diags)
  }
  percentage <- perc_resid_in_envl(model_diags)
  p_value <- model_diags$p

  return(list(
    model_diags = model_diags,
    percentage = percentage,
    p_value = p_value
  ))
}



remove_outliers <- function(
    observed_data,
    modeltype = "full",
    save_outliers = "",
    ncores = 1,
    epsilon = 1e-4,
    plots = FALSE) {
  # if we're calculating the additive model,
  # we get the outliers from the residuals of the full model.
  # Thus we need to quicky fit the full model first....
  model <- mlcm(observed_data,
    model = "full",
    method = "glm.fit",
    lnk = "probit",
    control = glm.control(epsilon = epsilon)
  )

  # we get the vector of residuals (deviance residual)
  deviance_residuals <- residuals(model$obj)
  s <- sort(abs(deviance_residuals),
    decreasing = TRUE,
    index.return = TRUE
  ) # return sorted value AND index

  finished <- FALSE
  start <- 1
  while (!finished) {
    cat("***********************************************************************\n")
    cat("*** iteratively removing putative outliers (trials with high residuals)\n")
    cat("     to improve goodnesss of fit **************************************\n")

    # select first trials
    trimmed_data <- observed_data[sort(s$ix[start:nrow(observed_data)]), ]

    removed <- observed_data[s$ix[1:start - 1], ]
    if (!save_outliers == "") {
      write.csv(removed, save_outliers, quote = FALSE, row.names = TRUE)
    }
    cat(paste("dataset reduced to -> ", nrow(trimmed_data), " trials \n", sep = ""))
    cat(paste("removed -> ", nrow(removed), " trials \n", sep = ""))

    model <- mlcm(trimmed_data,
      model = modeltype,
      method = "glm.fit",
      lnk = "probit",
      control = glm.control(epsilon = epsilon)
    )

    # evaluate GoF
    gof <- goodness_of_fit(model, epsilon = epsilon, ncores = ncores, plots = plots)
    cat("goodness of fit measures:\n")
    cat(paste("- percentage inside envelope CDF deviance residuals: ",
      gof$percentage,
      "\n",
      sep = ""
    ))
    cat(paste("- p-value of number of runs histogram: ", gof$p_value, "\n", sep = ""))

    # if p-val <0.05 then take one trial less (start +=1)
    if (gof$p_value < 0.05) {
      cat("...eliminating one more trial... \n\n")
      start <- start + 1
    } else { # if p-val >=0.05, break out of loop
      cat("...p-value >= 0.05, iteration finished.\n\n")
      finished <- TRUE
    }
  } # end while

  return(list(
    model = model,
    trimmed_data = trimmed_data,
    gof = gof
  ))
}


bootstrap_CIs <- function( # nolint: object_name_linter.
    model,
    modeltype,
    normalized = FALSE,
    save_samples = "",
    nsim = 1000,
    ncores = 1,
    epsilon = 1e-4) {
  # Bootstrap sample
  bootstrap <- pboot.mlcm(model,
    nsim = nsim,
    ncores = ncores,
    control = glm.control(epsilon = epsilon)
  )

  # Calculate 95% percentile confidence intervals from the bootstrap samples
  samples <- bootstrap$boot.samp

  # getting number of contexts
  n_contexts <- as.integer(ncol(model$pscale))

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

  # save bootstrap samples in CSV file as well
  if (!save_samples == "") {
    write.csv(t(samples), file = save_samples)
  }

  # samples a matrix of size n params x n boostrap samples
  # we then calculate for each row (each parameter) the percentiles
  bootsample_low <- c(0, apply(samples, 1, quantile, probs = 0.025))
  bootsample_high <- c(0, apply(samples, 1, quantile, probs = 0.975))

  # reformat to a matrix
  dim(bootsample_low) <- c(length(bootsample_low) / n_contexts, n_contexts)
  dim(bootsample_high) <- c(length(bootsample_high) / n_contexts, n_contexts)

  return(list(
    bootstrap = bootstrap,
    CI_low = bootsample_low,
    CI_high = bootsample_high
  ))
}


#' Pivot dataframe of scale-values to long-format
#'
#' @param scalevalues dataframe of scalevalues in wide format
#'
#' @return long-fromat of scale values (1 column per context)
pivot_scales <- function(scalevalues) {
  scalevalues_long <- reshape(scalevalues,
    varying = c("Context.1", "Context.2"),
    timevar = "context", v.names = "scale", direction = "long"
  )
  scalevalues_long <- subset(scalevalues_long, select = -id) # removing id column

  return(scalevalues_long)
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
#' epsilon is the resolution given to the optimization routine. At a difference
#' of epsilon is where the algorithm stops. We have issues with {mlcm}'s default
#' epsilon for the full model (1e-4). It tends to be stuck at local minima
#' and overestimates the scale values. This happens particularly bad for the
#' bootstrap samples. I (GA) manually and by hand decreased the epsilon value
#' to a value that does not give those results. It's a hack but it seems
#' to work. Alternatively one would have to try another optimization algorithm
#' more robust to local minima.
#'
estimate_scales <- function(filepath,
                            modeltype = "full",
                            do_bootstrap = FALSE,
                            nsim = 1000,
                            remove_outliers = FALSE,
                            plotflag = FALSE,
                            normalized = FALSE,
                            savecsv = FALSE,
                            saverds = FALSE,
                            epsilon = 1e-4,
                            ncores = 4) {
  cat("********** Estimating scales - START **********\n")
  filename <- basename(filepath)
  rootname <- strsplit(filename, ".csv")[[1]]
  directory <- dirname(filepath)

  # Load data
  observed_data <- read.csv(filepath, sep = ",")[c("Resp", "I1", "I2", "C1", "C2")]
  cat(paste("number of trials:", nrow(observed_data), sep = " "))

  # Estimating perceptaul scales
  model <- mlcm(observed_data,
    model = modeltype,
    method = "glm.fit",
    lnk = "probit",
    control = glm.control(epsilon = epsilon)
  )
  print(model)
  if (plotflag) {
    plot(model, type = "b")
  }

  # Remove trials with high residuals (full model) and refit model
  if (remove_outliers) {
    if (savecsv) {
      outliers_file <- file.path(directory, paste(rootname, ".outliers.csv", sep = ""))
    }
    removal <- remove_outliers(observed_data,
      modeltype = modeltype,
      save_outliers = outliers_file,
      ncores = ncores,
      epsilon = epsilon,
      plots = plotflag
    )
    model <- removal$model
    trimmed_data <- removal$trimmed_data
    gof <- removal$gof
    if (savecsv) {
      trimfix <- "-trimmed"
      write.csv(trimmed_data,
        file.path(directory, paste(rootname, trimfix, ".csv", sep = "")),
        quote = FALSE, row.names = FALSE
      )
    }
  } else {
    trimfix <- ""
  }

  # Extract scale values, reformatting names of rows and columns
  scalevalues <- model$pscale
  colnames(scalevalues) <- c("Context.1", "Context.2")
  for (i in 1:nrow(scalevalues)) {
    rownames(scalevalues)[i] <- i
  }
  if (modeltype == "add") {
    additiveshift <- model$obj$coefficients[length(model$obj$coefficients)]
    scalevalues[, 2] <- scalevalues[, 1] + additiveshift
  }


  # Normalize the scale values
  if (normalized) {
    scalevalues <- scalevalues / scalevalues[nrow(scalevalues), 2]
    normsuffix <- "-norm"
  } else {
    normsuffix <- ""
  }

  # Reformat to long-format
  scalevalues <- data.frame(intensity = row.names(scalevalues), scalevalues)
  scalevalues <- pivot_scales(scalevalues)

  # Bootstrap CIs
  if (do_bootstrap) {
    cat("bootstrapping the model to calculate confidence intervals\n")

    filepath_bootsamples <- file.path(
      directory,
      paste(rootname, trimfix, "-", modeltype, normsuffix,
        ".bootsamples.csv",
        sep = ""
      )
    )
    bootstrap <- bootstrap_CIs(model,
      modeltype,
      normalized = normalized,
      save_samples = filepath_bootsamples,
      nsim = nsim,
      ncores = ncores,
      epsilon = epsilon
    )

    # Format CI bounds same as scale values
    ci_low <- data.frame(intensity = 1:nrow(bootstrap$CI_low), bootstrap$CI_low)
    colnames(ci_low) <- c("intensity", "Context.1", "Context.2")
    ci_low <- pivot_scales(ci_low)

    ci_high <- data.frame(intensity = 1:nrow(bootstrap$CI_high), bootstrap$CI_high)
    colnames(ci_high) <- c("intensity", "Context.1", "Context.2")
    ci_high <- pivot_scales(ci_high)

    # Merge scale values, CI bounds
    tmp <- merge(scalevalues, ci_low, by = c("intensity", "context"), sort = FALSE)
    scalevalues <- merge(tmp, ci_high, by = c("intensity", "context"), sort = FALSE)

    colnames(scalevalues) <- c("intensity", "context", "scale", "scale_CI_low", "scale_CI_high")
  }

  # Save to Rda
  if (saverds) {
    filepath_rda <- file.path(
      directory,
      paste(rootname, trimfix, "-", modeltype,
        ".Rda",
        sep = ""
      )
    )
    print(paste("saving in..", filepath_rda, sep = ""))
    if (do_bootstrap && remove_outliers) {
      save(model, bootstrap, gof, file = filepath_rda)
    } else if (do_bootstrap) {
      save(model, bootstrap, file = filepath_rda)
    } else if (remove_outliers) {
      save(model, gof, file = filepath_rda)
    } else {
      save(model, file = filepath_rda)
    }
  }

  # Export to CSV
  if (savecsv) {
    filepath_scales <- file.path(
      directory,
      paste(rootname, trimfix, "-", modeltype, normsuffix,
        ".scales.csv",
        sep = ""
      )
    )
    write.csv(scalevalues, file = filepath_scales, row.names = FALSE, quote = FALSE)
  }

  cat("********** Estimating scales - END **********\n")
  cat("*********************************************\n")
  return(model)
}
