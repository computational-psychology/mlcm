library(MLCM)

df <- BumpyGlossy
colnames(df) <- c(
  "Resp",
  "glossiness_1",
  "glossiness_2",
  "bumpiness_1",
  "bumpiness_2"
)

write.csv(
  df,
  "tests/example_datasets/wrangled_BumpyGlossy.csv",
  row.names = FALSE,
  quote = FALSE
)

# Fit the MLCM model
model <- mlcm(df, model = "full")
