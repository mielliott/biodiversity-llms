import pandas as pd
import numpy as np
from functools import reduce
smk = snakemake # type: ignore

backbone_path = smk.input.backbone
predictions_path = smk.input.predictions
scores_path = smk.output[0]

taxonomy = (
    pd.read_csv(backbone_path, sep="\t", dtype=str)
    .map(str.lower)
    .set_index("id", drop=False)
)

taxonomy.rename(
    columns={x: x[:-4] for x in taxonomy.columns if "_key" in x}, inplace=True
)

rank_predictions = pd.read_csv(predictions_path, sep="\t", dtype=str, index_col=0).map(
    str.lower
)

name_to_id_cache = {}


def name_to_id(name, rank):
    name_id = name_to_id_cache.get(f"{rank},{name}")
    if name_id is None:
        # Assume all homonyms point to the same accepted key, so just take the first one
        name_id = taxonomy[
            (taxonomy["canonical_name"] == name) * (taxonomy["rank"] == rank)
        ][rank].get(0)
        name_to_id_cache[f"{rank},{name}"] = name_id
    return name_id


def count(iterable):
    return reduce(lambda a, b: a + 1, iterable, 0)


def score_one(r_taxon_id, s_taxon_id, query_rank) -> bool:
    return taxonomy.loc[s_taxon_id][query_rank] == r_taxon_id


def score(rank_prediction) -> pd.Series:
    s_taxon_id = name_to_id(rank_prediction["taxon"], rank_prediction["subject rank"])
    query_rank = rank_prediction["query rank"]
    ids = list(
        filter(
            lambda x: x != None,
            [
                name_to_id(response, query_rank)
                for response in rank_prediction["responses"].split(",")
            ],
        )
    )

    return pd.Series(
        {
            "num_correct": np.nan
            if s_taxon_id == None
            else count(
                filter(lambda x: x == taxonomy.loc[s_taxon_id][query_rank] == x, ids)
            ),
            "num_response": len(ids),
        }
    )


def dereference(id: str) -> str:
    return str(taxonomy["canonical_name"].get(id, ""))


def dereference_all(id_df: pd.Series):
    return id_df.apply(dereference)

i = 0
def score_with_progress(x, n):
    global i
    i += 1
    print(f"{i}/{n}\t{i / n:.0%}", end="\r", flush=True)
    return score(x)


n = len(rank_predictions)
scores = rank_predictions.apply(lambda x: score_with_progress(x, n), axis=1)
scores.to_csv(scores_path, sep="\t")
