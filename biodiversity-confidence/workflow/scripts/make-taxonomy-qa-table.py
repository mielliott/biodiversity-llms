import pandas as pd

rank_inputs = snakemake.input
query_table = snakemake.output[0]
ranks = snakemake.params.ranks

df = pd.DataFrame(columns=["subject_rank", "object_rank", "taxon"])

for subject_rank, path in rank_inputs.items():
    rank_df = pd.read_csv(path, sep="\t")
    subject_rank = subject_rank.rstrip("_") # Added a _ to "class" to avoid conflict with Python's keyword
    rank_df["subject_rank"] = subject_rank
    query_ranks = pd.Series(ranks[:ranks.index(subject_rank)], name="object_rank")
    df = pd.concat([df, rank_df.join(query_ranks, how="cross")])

df.to_csv(query_table, sep="\t", index=False)
