# from Carolin's scripts in crispenningEffect/inWork

drawGoodnessPlot <- function(x, ml, headline) {
  nsim <- dim(x$resid)[1]
  n <- dim(x$resid)[2]

  alpha <- 0.025
  # par(mfrow = c(1, 2))
  # mainText <- ifelse(simplePlot, "Goodness of simple Experiment","Goodnesss of variegated experiment")
  plot(sort(x$Obs.resid), (1:n - 0.5) / n,
    main = headline,
    ylab = "Cumulative Density Function",
    xlab = "Deviance Residuals", cex = 0.20
  )
  lines(x$resid[alpha * nsim, ], (1:n - 0.5) / n, col = "blue") # upper line
  lines(x$resid[(1 - alpha) * nsim, ], (1:n - 0.5) / n, col = "blue") # lower line

  # choose if plotting simpleData or variegatedData
  # if(simplePlot){
  #   obj <- s_m
  # } else {
  #   obj <- v_m
  # }
  obj <- ml


  # obj <- obs.mlds
  rs <- residuals(obj$obj, type = "deviance")
  fv.sort <- sort(fitted(obj), index.return = TRUE)
  rs <- rs[fv.sort$ix]
  rs <- rs > 0
  obs.runs <- sum(rs[1:(n - 1)] != rs[2:n])

  hist(x$NumRuns,
    xlab = "Number of Runs", main = "",
    breaks = "Sturges"
  )
  abline(v = x$ObsRuns, lwd = 2)
}


evaluateResiduals <- function(x) {
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
  fitProbs <- (nfit * 100) / length(splObs$x)
  return(fitProbs)
}


daf <- function(obj) {
  val <- (obj$null.deviance - obj$deviance) / obj$null.deviance
  return(val)
}
