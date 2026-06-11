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

# Long format: G, B, pscale
scales_long <- data.frame(
  glossiness = rep(seq_len(nrow(model$pscale)), each = ncol(model$pscale)),
  bumpiness = rep(seq_len(ncol(model$pscale)), times = nrow(model$pscale)),
  scale = as.vector(t(model$pscale))
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
