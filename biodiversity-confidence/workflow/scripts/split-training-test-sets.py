import numpy as np
import pandas as pd
smk = snakemake # type: ignore

# TODO: cv instead
# split_rank = smk.params.split_rank
# split_test_fraction = smk.params.split_test_fraction # Fraction of queries (grouped by taxons) to set aside as a test set

df = pd.read_csv(open(smk.input[0]), sep="\t")
df["target"] = (df["present"] == "Yes").astype(int) * 2 - 1
df[smk.params.query_fields + ["target"]].drop_duplicates()

# Drop fungi
df = df[~(df["kingdom"] == "fungi")]

# Drop records with unexpected genus names
weird_genera = df["genus"].apply(lambda s: s.isalnum()) == False
df = df[~weird_genera]

# TODO: cv instead
# shuffled_taxons = df[split_rank].unique()
# rng = np.random.default_rng(smk.params.seed)
# rng.shuffle(shuffled_taxons)

# train_taxons = set(shuffled_taxons[:int(len(shuffled_taxons) * split_test_fraction)+1])
# test_taxons = set(shuffled_taxons) - train_taxons

# df["train"] = df[split_rank].isin(train_taxons)

df.drop(columns=["present"])\
    .to_csv(open(smk.output[0], "w"), sep="\t")
