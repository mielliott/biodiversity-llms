# All GBIF backbone versions are available at https://hosted-datasets.gbif.org/datasets/backbone/

# See https://api.gbif.org/v1/species/5386/synonyms?limit=50
#
# For an ID with rank RANK, the accepted ID seems to be under RANK_key
# e.g. if ID1 is a synonym of ID2, rank RANK, both should have the same RANK_key that indicates which one is considered "accepted"

import pandas as pd

raw_backbone = snakemake.input[0]
dereferenced_backbone = snakemake.output[0]

RANKS = [
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species"
]

raw = pd.read_csv(open(full_backbone, "r"), sep="\t", dtype=str, names=[
    "id",
    "status",
    "rank",
    "kingdom_key",
    "phylum_key",
    "class_key",
    "order_key",
    "family_key",
    "genus_key",
    "species_key",
    "name_id",
    "scientific_name",
    "canonical_name"
])

id_map = raw[["id", "canonical_name"]].set_index("id")["canonical_name"].str.lower().to_dict()

table = raw[raw["rank"] == "SPECIES"][["id"]].copy()
for rank in RANKS:
    key = f"{rank}_key"
    table[rank] = raw[key].map(lambda x: id_map[x] if x in id_map else "")
table = table.set_index("id")

table.to_csv(dereferenced_backbone, sep="\t")
