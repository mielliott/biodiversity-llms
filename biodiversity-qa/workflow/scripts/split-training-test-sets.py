import numpy as np
import pandas as pd

split_rank = snakemake.params.split_rank
split_test_fraction = snakemake.params.split_test_fraction # Fraction of queries (grouped by taxons) to set aside as a test set

df = pd.read_csv(open(snakemake.input[0]), sep="\t")
df["target"] = (df["present"] == "Yes").astype(int) * 2 - 1
df[snakemake.params.query_fields + ["target"]].drop_duplicates()

# Drop fungi
df = df[~(df["kingdom"] == "fungi")]

shuffled_taxons = df[split_rank].unique()
rng = np.random.default_rng(snakemake.params.seed)
rng.shuffle(shuffled_taxons)

train_taxons = set(shuffled_taxons[:int(len(shuffled_taxons) * split_test_fraction)+1])
test_taxons = set(shuffled_taxons) - train_taxons

df["train"] = df[split_rank].isin(train_taxons)

df.to_csv(open(snakemake.output[0], "w"), sep="\t")
