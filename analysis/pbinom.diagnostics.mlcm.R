pbinom.diagnostics <- function(obj, nsim = 200, type = "deviance", no.warn = TRUE, workers="localhost", master="localhost", ...) 
	{
    # working with snow
    # initialize cluster
    cl <- makeSOCKcluster(workers, master= master)
   
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

