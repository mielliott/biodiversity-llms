import pandas as pd
import numpy as np
smk = snakemake # type: ignore

report_tsv = smk.input[0]
alignments_tsv = smk.output[0]
bad_names_tsv = smk.output[1]

def clean_name(name):
    if type(name) == str:
        split = name.lstrip().split()
        return split[0].lower() if len(split) > 0 else ""
    else:
        return np.nan

def clean_path(path):
    if type(path) == str:
        return "|".join([clean_name(x) for x in path.split("|")])
    else:
        return np.nan
    
raw = pd.read_csv(report_tsv, sep="\t", dtype=str)\
    [["providedName", "alignedName", "alignedRank", "alignedCommonNames", "alignedPath", "alignedPathNames"]]

# Find names with no matches by nomer
bads = raw.groupby("providedName")["alignedPath"].count() == 0
bads = bads[bads].reset_index()["providedName"]
bads.to_csv(bad_names_tsv, sep="\t", index=False)

raw = raw.iloc[raw["alignedPathNames"].dropna().index]

data = pd.DataFrame(index=raw.index)
data["providedName"] = raw["providedName"].map(clean_name)
data["alignedName"] = raw["alignedName"].map(clean_name)
data["alignedRank"] = raw["alignedRank"].map(clean_name)
data["alignedPath"] = raw["alignedPath"].map(clean_path)
data["alignedPathNames"] = raw["alignedPathNames"].map(clean_path)

# Build alias lists, map all aliases of each name to a shared set
# Matches names across different kingdoms/ranks, but that's okay - they aren't disambiguated in our question set
aliases = data.groupby(["providedName"])["alignedName"].agg(lambda x: set(x))
for name, name_aliases in aliases.items():
    it_aliases = [x for x in name_aliases]
    for alias in it_aliases:
        if alias != name and alias in aliases:
            name_aliases.update(aliases[alias])
            aliases[alias] = name_aliases

all_paths = data.groupby("providedName")[["alignedPath", "alignedPathNames"]]\
    .aggregate(lambda x: "|".join(x))\
    .apply(axis=1, func=lambda r: set(zip(r["alignedPathNames"].split("|"), r["alignedPath"].split("|"))))

df = pd.DataFrame()
df["name"] = aliases.keys()
df["aliases"] = df["name"].map(lambda x: aliases[x])
df["classification"] = df["name"].map(lambda x: all_paths[x])

df.to_csv(alignments_tsv, sep="\t", index=False)
