library(MLCM)

df <- GlossyBumpy
colnames(df) <- c(
  "Resp",
  "glossiness_1",
  "glossiness_2",
  "bumpiness_1",
  "bumpiness_2"
)

write.csv(
  df,
  "tests/example_datasets/wrangled_GlossyBumpy.csv",
  row.names = FALSE,
  quote = FALSE
)

# Fit the MLCM model
model <- mlcm(df, model = "full")

# Run bootstrap
set.seed(123)
bootstrap <- boot.mlcm(model, nsim = 1000)
samples <- bootstrap$boot.samp

# Calculate for each row (each parameter) the percentiles
bootstrap$CI_low <- c(0, apply(samples, 1, quantile, probs = 0.025))
bootstrap$CI_high <- c(0, apply(samples, 1, quantile, probs = 0.975))

# Reformat to same shape as scale values
dim(bootstrap$CI_low) <- dim(model$pscale)
dim(bootstrap$CI_high) <- dim(model$pscale)


# Long format: G, B, pscale
scales_long <- data.frame(
  glossiness = rep(seq_len(nrow(model$pscale)), each = ncol(model$pscale)),
  bumpiness = rep(seq_len(ncol(model$pscale)), times = nrow(model$pscale)),
  scale = as.vector(t(model$pscale)),
  CI_low = as.vector(t(bootstrap$CI_low)),
  CI_high = as.vector(t(bootstrap$CI_high))
)

# Sort by B then G
scales_long <- scales_long[
  order(scales_long$bumpiness, scales_long$glossiness),
]

write.csv(
  scales_long,
  "tests/example_datasets/scales_GlossyBumpy.csv",
  row.names = FALSE,
  quote = FALSE
)


# Normalize the scales to 0-1 range
scales_long$scale_norm <- scales_long$scale / max(scales_long$scale)

# CIs for normalized scales
samples_norm <- apply(samples, 2, function(smpl) smpl / max(smpl))

bootstrap$CI_low_norm <- c(0, apply(samples_norm, 1, quantile, probs = 0.025))
bootstrap$CI_high_norm <- c(0, apply(samples_norm, 1, quantile, probs = 0.975))

dim(bootstrap$CI_low_norm) <- dim(model$pscale)
dim(bootstrap$CI_high_norm) <- dim(model$pscale)

scales_long$CI_low_norm <- as.vector(t(bootstrap$CI_low_norm))
scales_long$CI_high_norm <- as.vector(t(bootstrap$CI_high_norm))

write.csv(
  scales_long,
  "tests/example_datasets/scales_GlossyBumpy.csv",
  row.names = FALSE,
  quote = FALSE
)
