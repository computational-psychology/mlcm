#### MLCM analysis
analyzemlcm <- function(rootname) {
    library('MLCM')
    source("pboot.mlcm.R")

    df <- read.csv(paste(rootname, '.csv', sep = ""), sep = ',')
    keeps <- c("Resp", "L1", "L2", "C1", "C2")
    df1 <- df[keeps]
    print(nrow(df1))
  

    ### estimating the scales
    bg.full <- mlcm(df1, model = "full", method='glm.fit', lnk='probit', control=glm.control(epsilon=1e-4))
    print(bg.full)
    # scale values are:
    bg.scales <- bg.full$pscale
    
    #plot(bg.full, type='b')
    
    ### calculating confidence intervals
    print('bootstrapping the model to calculate confidence intervals')
    
    # we first bootstrap the model
    bg.full.boot <- boot.mlcm(bg.full, nsim=1000, control=glm.control(epsilon=1e-4))

    # we manually calcualate the percentile confidence intervals from the bootstrap samples
    # with 95 % confidence
    samples <- bg.full.boot$boot.samp
    
    # getting number of contexts 
    nc <- as.integer(ncol(bg.full$pscale))
    
    bg.low <- c(0, apply(bg.full.boot$boot.samp, 1, quantile, probs = 0.025))
    dim(bg.low) <- c(length(bg.low)/nc, nc)

    bg.high <- c(0, apply(bg.full.boot$boot.samp, 1, quantile, probs = 0.975))
    dim(bg.high) <- c(length(bg.high)/nc, nc)

    # the confidence intervals for each scale estimate are
    # lower bound:
    #print(bg.low)

    # upper bound:
    #print(bg.high)

    save(bg.full, bg.full.boot, bg.scales, bg.low, bg.high, file=paste(rootname, '.glm.MLCM', sep = ""))
    print('Done')

}


# EOF
