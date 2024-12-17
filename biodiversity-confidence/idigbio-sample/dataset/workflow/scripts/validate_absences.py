import csv
import sys
from typing import Any
import requests as rq

args = iter(sys.argv[1:])
API = str(next(args))


def make_species_location_query(record):
    print(record, file=sys.stderr)
    return {
        "rq": {
            "kingdom": str(record["kingdom"]),
            "genus": str(record["genus"]),
            "specificepithet": str(record["specificepithet"]),
            "country": str(record["country"]),
            "stateprovince": str(record["stateprovince"]),
            "county": str(record["county"]),
        },
        "limit": 1,
        "offset": 0,
    }


tsv_args: dict[str, Any] = dict(
    delimiter="\t",
    lineterminator="\n",
    escapechar="\\",
    quoting=csv.QUOTE_NONE
)

unvalidated_absences = csv.DictReader(sys.stdin, **tsv_args)
absence_validations = csv.DictWriter(sys.stdout, ["valid"], **tsv_args)
absence_validations.writeheader()

for record in unvalidated_absences:
    query = make_species_location_query(record)
    response = rq.post(f"{API}/search/records", json=query)
    valid = response.json()["itemCount"] == 0
    absence_validations.writerow({"valid": valid})
