import requests as rq
import pandas as pd
from snakemake.script import Snakemake

smk: Snakemake = snakemake  # type: ignore

file_in = smk.input[0]
file_out = smk.output[0]


def make_species_location_query(record):
    return {
        "rq": {
            "kingdom": str(record.kingdom),
            "genus": str(record.genus),
            "specificepithet": str(record.specificepithet),
            "country": str(record.country),
            "stateprovince": str(record.stateprovince),
            "county": str(record.county),
        },
        "limit": 1,
        "offset": 0,
    }


absences = pd.read_csv(open(file_in), sep="\t")

n = len(absences)
responses = {}
for record in absences.itertuples():
    query = make_species_location_query(record)
    response = rq.post("http://search.idigbio.org/v2/search/records/", json=query)
    responses[record.Index] = response.json()["itemCount"]
    print(f"{record.Index}, {len(responses)} / {n}", end="\r", flush=True)

absence_matches = pd.Series(responses)
m = sum(absence_matches == 0)
print(f"Records missing location: {m}/{n} ({100 * m / n:2.2f}%)")

absences["valid"] = absence_matches == 0
absences["valid"].to_csv(open(file_out, "w"), sep="\t")
