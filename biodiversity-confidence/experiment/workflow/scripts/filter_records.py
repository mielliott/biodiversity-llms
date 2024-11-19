import pandas as pd
from snakemake.script import Snakemake

smk: Snakemake = snakemake  # type: ignore[undefined-variable]

UNFILTERED_TSV = smk.input[0]
FILTERED_TSV = smk.output[0]

df = pd.read_csv(open(UNFILTERED_TSV, "r"), sep="\t").dropna()
df = df[~(df == "[Not Stated]").any(axis=1)]
df = df.map(lambda x: str(x).strip("[]").lower())
fields = ["genus", "country", "stateprovince", "county"]
df[fields] = df[fields].map(lambda x: x.title())

df.groupby(["kingdom", "family"]).head(300).to_csv(FILTERED_TSV, sep="\t", index=False)
