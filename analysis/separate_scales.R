#### MLCM analysis
separate_scales <- function(rootname, sset = "1-2") {
  # rootname <- 'sim_mlcm'
  # sset <- '1-2'

  # library('MLCM')

  fname <- paste(rootname, "_subset_", sset, ".csv", sep = "")

  df <- read.csv(fname, sep = ",")
  keeps <- c("Resp", "L1", "L2", "C1", "C2")
  df <- df[keeps]
  print(nrow(df))


  d <- df
  dX <- as.data.frame(lapply(d[, -1], as.factor))
  f1 <- as.formula("~ L1 + 0")
  f2 <- as.formula("~ L2 + 0")
  mm1 <- model.matrix(f1, dX)
  mm2 <- model.matrix(f2, dX)

  # X <- (mm2 - mm1)
  X <- (mm1 - mm2)[, -1] # drops first entry

  resp <- d$Resp
  d.df <- data.frame(Resp = resp, X)


  psc.glm <- glm(Resp ~ . - 1, binomial(link = "probit"), d.df, control = glm.control(maxit = 50000, epsilon = 1e-14))
  print(psc.glm)

  psc.glm$coefficients
}

# EOF
