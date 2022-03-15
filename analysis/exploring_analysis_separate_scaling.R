##  Exploting MLCM internals, how the design matrix is built, and how to compare additive and full model
# for experiment on White's stimulus 
library('MLCM')

setwd("~/git/white_scaling/analysis")
# options(warn=1)

obsname <- 'ga6'

lnk = 'probit' # 'probit' is default, 'logit' as alternative

epsilon <- 1e-4

rootname = paste('../data/parsed_results/', obsname, '_reindexed','_subset_', '1-2', sep = '')
fname <- paste(rootname, '.csv', sep = "")
               
df <- read.csv(fname, sep = ',')
keeps <- c("Resp", "L1", "L2", "C1", "C2")
df <- df[keeps]
print(nrow(df))


d <- df
dX <- as.data.frame(lapply(d[, -1], as.factor))
f1 <- as.formula('~ L1 + 0')
f2 <- as.formula('~ L2 + 0')
mm1 <- model.matrix(f1, dX) 
mm2 <- model.matrix(f2, dX) 

#X <- (mm2 - mm1)
X <- (mm1 - mm2)[, -1] # drops first entry


resp <- d$Resp
d.df <- data.frame(Resp = resp, X)


psc.glm <- glm(Resp ~ . - 1, binomial(link = lnk), d.df, control = glm.control(maxit = 50000, epsilon = 1e-14))
print(psc.glm)





##### MLCM analysis - additive vs. saturated

# full MLCM
# reads data
fname <- paste('../data/parsed_results/', obsname, '_reindexed', '.csv', sep = "")
df_full <- read.csv(fname, sep = ',')
keeps <- c("Resp", "L1", "L2", "C1", "C2")
df_full <- df_full[keeps]
print(nrow(df_full))

# fits saturated model
bg.full <- mlcm(df_full, model = "full", method='glm.fit', control=glm.control(epsilon=epsilon))
print(bg.full)
plot(bg.full)

# fits additive model
bg.add <- mlcm(df_full, model = "add", method='glm.fit', control=glm.control(epsilon=epsilon))
print(bg.add)
plot(bg.add)

# likelihood ratio test between the two models
anova(bg.add, bg.full, test = "Chisq")

# if significant, it means that saturated (full) model explains better the data 
# than the additive model, i.e. there is signifficant interactions between the
# stimulus dimensions

