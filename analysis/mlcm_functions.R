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

#' Evaluate Goodness-of-Fit.
#'
#' @param model {mlcm} model-object
#' @param ncores number of cores. Default 1.
#' @param plots TRUE or FALSE, whether to do GoF plots or not.
goodness_of_fit <- function(model, ncores = 1, plots = FALSE) {
  model_diags <- pbinom.diagnostics(model,
    nsim = 1000, ncores = ncores,
    control = model$obj$control
  )
  if (plots) {
    plot(model_diags)
  }
  model_diags$percentage <- perc_resid_in_envl(model_diags)

  return(model_diags = model_diags)
}


#' Iteratively remove trials with highest residuals (putative outliers) until a "good" GoF.
#'
#' @param observed_data dataframe with all trials
#' @param model estimated model to improve GoF for
#' @param ncores number of cores. Default 1.
#' @param plots TRUE or FALSE, whether to do GoF plots or not.
remove_outliers <- function(
    observed_data,
    model,
    ncores = 1,
    plots = FALSE) {
  # Extract vector of residuals (deviance residual)
  deviance_residuals <- residuals(model$obj)
  deviance_residuals <- sort(abs(deviance_residuals), decreasing = TRUE, index.return = TRUE) # return sorted value AND index

  # Evaluate GoF
  gof <- goodness_of_fit(model, ncores = ncores, plots = plots)
  cat("\nGoodness-of-Fit measures:\n")
  cat(paste("- percentage inside envelope CDF deviance residuals:", gof$percentage, "\n"))
  cat(paste("- p-value of number of runs histogram:", gof$p, "\n"))

  if (gof$p < 0.05) {
    cat("\n***********************************************************************\n")
    cat("*** Iteratively removing trials with high residuals to improve GoF ****\n")
    cat("***********************************************************************\n")
  }
  start <- 1
  trimmed_data <- observed_data[sort(deviance_residuals$ix[start:nrow(observed_data)]),]
  outliers <- observed_data[deviance_residuals$ix[1:start - 1], ]
  while (gof$p < 0.05) {
    start <- start + 1
    cat("\n...trimming one more trial...\n")

    # Remove outlier
    trimmed_data <- observed_data[sort(deviance_residuals$ix[start:nrow(observed_data)]), ]
    outliers <- observed_data[deviance_residuals$ix[1:start - 1], ]
    cat(paste("dataset trimmed to ->", nrow(trimmed_data), "trials\n"))
    cat(paste("removed ->", nrow(outliers), "trials\n"))

    # Fit model on trimmed data
    model <- mlcm(trimmed_data,
      model = model$model,
      method = model$obj$method,
      lnk = model$link,
      control = model$obj$control
    )

    # Evaluate Goodness-of-Fit
    gof <- goodness_of_fit(model, ncores = ncores, plots = plots)
    cat("\nGoodness-of-Fit measures:\n")
    cat(paste("- percentage inside envelope CDF deviance residuals:", gof$percentage, "\n"))
    cat(paste("- p-value of number of runs histogram:", gof$p, "\n"))
  }
  cat("\n***********************************************************************\n")
  cat(paste("p =", gof$p, ">= 0.05, iteration finished.\n\n"))

  return(list(
    model = model,
    trimmed_data = trimmed_data,
    outliers = outliers,
    gof = gof
  ))
}

#' Confidence Intervals (95%) for scale values, from bootstrapping & percentile method
#'
#' @param model {mlcm} model-object
#' @param nsim number of bootstrap samples. Default=1000
#' @param normalized TRUE or FALSE. TRUE if resulting scales should be normalized
#'                    to their maximum. Default: FALSE
#' @param ncores number of cores. Default 1.
#'
#' @returns `bootstrap` object, with additional attributes:
#'          * `CI_low` (number),
#'          * `CI_high` (number)
#'
#' We have issues with {mlcm}'s default epsilon for the full model (1e-8).
#' It tends to be stuck at local minima and overestimates the scale values.
#' This happens particularly bad for the bootstrap samples.
#' I (GA) manually and by hand decreased the epsilon value
#' to a value that does not give those results.
#' It's a hack but it seems to work.
#' Alternatively one would have to try another optimization algorithm more robust to local minima.
bootstrap_CIs <- function( # nolint: object_name_linter.
    model,
    nsim = 1000,
    normalized = FALSE,
    ncores = 1) {
  # Bootstrap sample
  bootstrap <- pboot.mlcm(model,
    nsim = nsim,
    ncores = ncores,
    control = model$obj$control
  )

  # Extract bootstrap samples: matrix of size n_params x n_bootstrap_samples
  samples <- bootstrap$boot.samp
  if (model$model == "add") {
    # For the additive model, need rearranging to get the full matrix
    additiveshift <- samples[nrow(samples), ]

    context1 <- samples[1:nrow(samples) - 1, ]
    context2 <- rbind(rep(0, nsim), samples[1:nrow(samples) - 1, ]) + additiveshift

    samples <- rbind(context1, context2)
  }

  # Normalize by maximum in each row
  if (normalized) {
    samples <- apply(samples, 2, function(smpl) smpl / max(smpl))
  }

  # Calculate for each row (each parameter) the percentiles
  bootstrap$CI_low <- c(0, apply(samples, 1, quantile, probs = 0.025))
  bootstrap$CI_high <- c(0, apply(samples, 1, quantile, probs = 0.975))

  # Reformat to same shape as scale values
  dim(bootstrap$CI_low) <- dim(model$pscale)
  dim(bootstrap$CI_high) <- dim(model$pscale)

  bootstrap$samples <- samples
  return(bootstrap)
}


#' Extract and format scale values (and optionally combine with CIs)
#'
#' @param model {MLCM} model object to extract estimated scale values from
#' @param bootstrap bootstrap output, optional
#' @param normalized whether to normalize scale values, default FALSE
extract_scales <- function(model, bootstrap, normalized = FALSE) {
  # Extract scale values
  scale_values <- model$pscale |>
    as.data.frame(row.names = seq_along(model$pscale[, 1])) |>
    setNames(c("context.1", "context.2"))

  # If additive model, shift
  if (model$model == "add") {
    scale_values[, 2] <- scale_values[, 1] + scale_values[2, 2]
  }

  # Normalize scale values
  if (normalized) {
    scale_values <- scale_values / max(scale_values)
  }

  # Reformat
  scale_values$intensity <- seq_along(scale_values[, 1])
  scale_values <- scale_values |>
    reshape(
      direction = "long",
      varying = c("context.1", "context.2"), timevar = "context",
      v.names = "scale",
    ) |>
    subset(select = c("intensity", "context", "scale")) # removing id column, reordering

  # Include bootstrapped CI bounds
  if (!missing(bootstrap)) {
    # Format CI bounds same as scale values
    ci_low <-
      data.frame(intensity = seq_along(bootstrap$CI_low[, 1]), bootstrap$CI_low) |>
      setNames(c("intensity", "context.1", "context.2")) |>
      reshape(
        direction = "long",
        varying = c("context.1", "context.2"), timevar = "context",
        v.names = "scale_CI_low",
      )

    ci_high <-
      data.frame(intensity = seq_along(bootstrap$CI_high[, 1]), bootstrap$CI_high) |>
      setNames(c("intensity", "context.1", "context.2")) |>
      reshape(
        direction = "long",
        varying = c("context.1", "context.2"), timevar = "context",
        v.names = "scale_CI_high",
      )

    # Merge CI bounds with scale values
    ci_bounds <- merge(ci_low, ci_high, by = c("intensity", "context"), sort = FALSE)
    scale_values <- merge(scale_values, ci_bounds, by = c("intensity", "context"), sort = FALSE)
    scale_values <- subset(scale_values, select = c("intensity", "context", "scale", "scale_CI_low", "scale_CI_high"))
  }

  return(scale_values)
}


#' Estimate perceptual scales from data using MLCM
#'
#' @param observed_data dataframe of trials to estimate perceptual scales for
#' @param modeltype 'add' or 'full', for the type of model to be tested.
#'                  Default: full.
#' @param plotflag TRUE or FALSE, whether to do plots or not. Default: FALSE
#' @param epsilon Resolution for the optimization routines.
#'                At a difference of epsilon is where the algorithm stops. Default: 1e-4
#'
#' @returns {mlcm}-model object.
#'
#' We have issues with {mlcm}'s default epsilon for the full model (1e-8).
#' It tends to be stuck at local minima and overestimates the scale values.
#' This happens particularly bad for the bootstrap samples.
#' I (GA) manually and by hand decreased the epsilon value
#' to a value that does not give those results.
#' It's a hack but it seems to work.
#' Alternatively one would have to try another optimization algorithm more robust to local minima.
estimate_scales <- function(observed_data,
                            modeltype = "full",
                            plotflag = FALSE,
                            epsilon = 1e-4) {
  # Fit perceptual scales
  model <- mlcm(observed_data,
    model = modeltype,
    method = "glm.fit",
    lnk = "probit",
    control = glm.control(epsilon = epsilon)
  )
  if (plotflag) {
    plot(model, type = "b")
  }

  return(model)
}
