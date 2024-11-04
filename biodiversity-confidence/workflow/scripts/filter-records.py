import pandas as pd

smk = snakemake  # type: ignore

UNFILTERED_TSV = smk.input[0]
FILTERED_TSV = smk.output[0]

df = pd.read_csv(open(UNFILTERED_TSV, "r"), sep="\t").dropna()
df = df[~(df == "[Not Stated]").any(axis=1)]
df = df.applymap(lambda x: str(x).strip("[]").lower())  # type: ignore

fields = ["genus", "country", "stateprovince", "county"]
df[fields] = df[fields].applymap(lambda x: x.title())

df.groupby(["kingdom", "family"]).head(300).to_csv(FILTERED_TSV, sep="\t", index=None)
