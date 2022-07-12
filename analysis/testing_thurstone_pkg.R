library('psych')


# consider the case of 100 random orders
set.seed((42))
ranks <- matrix(NA,nrow=100,ncol=5)

for(i in 1:100) ranks[i,] <- sample(5,5)

t <- thurstone(ranks,TRUE)

t   #show the fits
t$choice #show the choice matrix