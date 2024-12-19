import csv
import os
import sys
from typing import Any
import concurrent.futures
import pandas as pd
import requests as rq

args = iter(sys.argv[1:])

LOCATIONS_PATH = str(next(args))
SHUFFLE_FIELDS = str(next(args)).split(",")
VALIDATION_FIELDS = str(next(args)).split(",")
MAX_RETRIES = int(next(args))
API = str(next(args))
RANDOM_STATE = int(next(args))

all_locations = pd.read_csv(LOCATIONS_PATH, sep="\t", usecols=SHUFFLE_FIELDS)

tsv_args: dict[str, Any] = dict(
    delimiter="\t",
    lineterminator="\n",
    escapechar="\\",
    quoting=csv.QUOTE_NONE
)

records = csv.DictReader(sys.stdin, **tsv_args)

if records.fieldnames is None:
    raise RuntimeError("Bad input!")

validated_absences = csv.DictWriter(sys.stdout, records.fieldnames, **tsv_args)
validated_absences.writeheader()


def make_species_location_query(record):
    return {
        "rq": {f: str(record[f]) for f in VALIDATION_FIELDS},
        "limit": 1,
        "offset": 0,
    }


random_box = [RANDOM_STATE]


def make_pseudo_absence(record):
    random_box[0] += 1
    for _, location in all_locations.sample(MAX_RETRIES, random_state=random_box[0]).iterrows():
        absence_record = record | location.to_dict()
        query = make_species_location_query(absence_record)
        response = rq.post(f"{API}/search/records", json=query)
        if response.json()["itemCount"] == 0:
            return absence_record
    return None


try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for absence_record in executor.map(make_pseudo_absence, records):
            if absence_record is not None:
                validated_absences.writerow(absence_record)
except BrokenPipeError:
    # Python prints a warning even if the error is caught. This silences the warning.
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(0)
