import csv
import itertools
import sys
from typing import Any, Sequence, cast
import concurrent.futures
import pandas as pd
import requests as rq

args = iter(sys.argv[1:])

LOCATIONS_PATH = str(next(args))
LOCATION_FIELDS = str(next(args))
MAX_RETRIES = int(next(args))
API = str(next(args))
RANDOM_STATE = int(next(args))

location_fields = LOCATION_FIELDS.split(",")
locations = pd.read_csv(LOCATIONS_PATH, sep="\t", usecols=location_fields)


tsv_args: dict[str, Any] = dict(
    delimiter="\t",
    lineterminator="\n",
    escapechar="\\",
    quoting=csv.QUOTE_NONE
)

records = csv.DictReader(sys.stdin, **tsv_args)

taxonomy_fields = list(records.fieldnames) if records.fieldnames is not None else []
fields = taxonomy_fields + location_fields

validated_absences = csv.DictWriter(sys.stdout, fields, **tsv_args)
validated_absences.writeheader()

match_fields = set(taxonomy_fields) | set(location_fields) - {"county"}


def make_species_location_query(record):
    return {
        "rq": {f: str(record[f]) for f in match_fields},
        "limit": 1,
        "offset": 0,
    }


random_box = [RANDOM_STATE]


def make_pseudo_absence(record):
    random_box[0] += 1
    for _, location in locations.sample(MAX_RETRIES, random_state=random_box[0]).iterrows():
        absence_record = record | location.to_dict()
        query = make_species_location_query(absence_record)
        response = rq.post(f"{API}/search/records", json=query)
        if response.json()["itemCount"] == 0:
            return absence_record
    return None


with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    for absence_record in executor.map(make_pseudo_absence, records):
        if absence_record is not None:
            validated_absences.writerow(absence_record)
