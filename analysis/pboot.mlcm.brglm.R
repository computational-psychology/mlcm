pboot.mlcm <- function(x, nsim, workers="localhost", master="localhost", ...){
  
  # working with snow
  cl <- makeSOCKcluster(workers, master= master)

  clusterEvalQ(cl, library(brglm))
  
  d <- as.matrix(x$obj$data[, -1])
  p <- fitted(x)
  rsim <- matrix(rbinom(length(p) * nsim, 1, p), 
                 nrow = length(p), ncol = nsim)
  
  clusterExport(cl, c("rsim", "d", "x"), envir= environment() )
  
  bts.samp <- parApply(cl, rsim, 2, function(y, dd) {
    psct <- brglm.fit(dd, y, family = binomial(x$link), ...)$coefficients
    names(psct) <- x$stimulus[-1]
    psct
  }, dd = d)
  
  stopCluster(cl)
  
  
  list(boot.samp = bts.samp, 
       bt.mean = apply(bts.samp, 1, mean), 
       bt.sd = apply(bts.samp, 1, sd), N = nsim)
}