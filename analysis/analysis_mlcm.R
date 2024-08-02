#### MLCM analysis
library(MLCM)
library(snow)
ncores <- 4
workers <- replicate(ncores, "localhost")
master <- "localhost"

source("scale_estimation/pboot.mlcm.R")
source("scale_estimation/gofutils.R")
source("scale_estimation/pbinom.diagnostics.mlcm.R")

analyzemlcm <- function(rootname, modeltype = "full", do_bootstrap = FALSE, nsim = 1000, fr = FALSE, thr = 2.5) {
  # epsilon is the resolution given to the optimization routine. At a difference
  # of epsilon is where the algorithm stops. We have issues with the default
  # epsilon for the full model. It tends to be stuck at local minima
  # and overestimates the scale values. This happens particularly bad for the
  # bootstrap samples. I manually and by hand decresed the epsilon value
  # to a value that does not give those results. It's a hack but it seems
  # to work. Alternatively one would have to try another optimization algorithm
  # more robust to local minima. G.A.
  # # default is epsilon = 1e-8.
  epsilon <- 1e-4

  df <- read.csv(paste(rootname, ".csv", sep = ""), sep = ",")
  keeps <- c("Resp", "L1", "L2", "C1", "C2")
  df1 <- df[keeps]
  print(nrow(df1))


  ### estimating the scales
  obs <- mlcm(df1, model = modeltype, method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))
  print(obs)

  # plot(obs, type='b')

  # refiting by filtering trials with high residuals. take the high residuals of the full model
  if (fr) {
    # if we're calculating the additive model, we get the outliers from the residuals of the full model.
    # thus we need to quicky fit the full model first....
    if (modeltype == "add") {
      obs <- mlcm(df1, model = "full", method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))
    }

    if (is.numeric(thr)) {
      # thr is arbitrary, thr = 2.5 in the book and in our previous work
      y <- df1[((residuals(obs$obj) > -thr) & (residuals(obs$obj) < thr)), ]
      print(paste("dataset reduced to -> ", nrow(y), sep = ""))

      obs <- mlcm(y, model = modeltype, method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))
    } else {
      # we get the vector of residuals (deviance residual)
      res <- residuals(obs$obj)
      s <- sort(abs(res), decreasing = TRUE, index.return = TRUE) # return sorted value AND index

      # first 10 indices with highest deviance residuals
      # res[s$ix[1:10]]

      finished <- FALSE
      start <- 1
      while (!finished) {
        # select first trials
        y <- df1[sort(s$ix[start:nrow(df1)]), ]

        removed <- df1[s$ix[1:start - 1], ]
        write.csv(removed, paste(rootname, "_removed.csv", sep = ""))

        print(paste("dataset reduced to -> ", nrow(y), sep = ""))
        print(paste("removed -> ", nrow(removed), sep = ""))

        obs <- mlcm(y, model = modeltype, method = "glm.fit", lnk = "probit", control = glm.control(epsilon = epsilon))

        # evaluate GoF
        obs.diags <- pbinom.diagnostics(obs,
          nsim = 1000, workers = workers, master = master,
          control = glm.control(epsilon = 1e-4)
        )

        # plot(obs.diags)


        # print the statistics
        per <- evaluateResiduals(obs.diags)
        p <- obs.diags$p
        print(paste("Percentage inside envelope CDF deviance residuals: ", per, sep = ""))
        print(paste("P-value of number of runs histogram: ", p, sep = ""))
        print(obs.diags$ObsRuns)

        # if p-val <0.05 then take one trial less (start +=1)
        if (p < 0.05) {
          print("eliminating one trial more... ")
          start <- start + 1
        } else { # if p-val >=0.05, break out of loop
          print("breaking loop")
          finished <- TRUE
        }

        # saving GOF data in diags.MLCM
        rootname2 <- paste(rootname, "_", modeltype, sep = "")
        suffixsave <- ".fr.glm.diags.MLCM"
        file2save <- paste(rootname2, suffixsave, sep = "")
        save(obs.diags, per, p, file = file2save)
      }
    }
    suffix <- ".fr.glm.MLCM"
  } else {
    suffix <- ".glm.MLCM"
  }


  # scale values are:
  obs.scales <- obs$pscale

  if (modeltype == "add") {
    additiveshift <- obs$obj$coefficients[length(obs$obj$coefficients)]
    obs.scales[, 2] <- obs.scales[, 1] + additiveshift
  }


  if (do_bootstrap) {
    ### calculating confidence intervals
    print("bootstrapping the model to calculate confidence intervals")

    # we first bootstrap the model
    obs.boot <- pboot.mlcm(obs, nsim = nsim, workers = workers, master = master, control = glm.control(epsilon = epsilon))

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


    # samples a matrix of size n params x n boostrap samples
    # we then calculate for each row (each parameter) the percentiles

    obs.low <- c(0, apply(samples, 1, quantile, probs = 0.025))
    obs.high <- c(0, apply(samples, 1, quantile, probs = 0.975))

    # reformat to a matrix
    dim(obs.low) <- c(length(obs.low) / nc, nc)
    dim(obs.high) <- c(length(obs.high) / nc, nc)


    # the confidence intervals for each scale estimate are
    # lower bound:
    # print(bg.low)

    # upper bound:
    # print(bg.high)

    save(obs, obs.boot, obs.scales, obs.low, obs.high, samples, file = paste(rootname, "_", modeltype, suffix, sep = ""))
    print(paste("saving in..", rootname, "_", modeltype, suffix, sep = ""))
  } else {
    save(obs, obs.scales, file = paste(rootname, "_", modeltype, suffix, sep = ""))
  }



  print("Done")
}


# EOF
