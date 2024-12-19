import csv
import re
import sys
from typing import Any, Optional
import pycountry

args = iter(sys.argv[1:])

OUTPUT_FIELDS = str(next(args)).split(",")


def clean_string(name: str):
    return (re.sub("[\\(\\[].*?[\\)\\]]", "", string=name)
            .replace(".", ""))


def get_country_by_code(code: str) -> Optional[str]:
    if len(code) == 2:
        country = pycountry.countries.get(alpha_2=code)
    else:
        country = pycountry.countries.get(alpha_3=code)
    if country is None:
        print("Countrycode:", code, file=sys.stderr)
    return country.name if country is not None else None


def look_up_country_name_by_code(record: dict[str, str]) -> Optional[str]:
    code = record["countrycode"]
    return get_country_by_code(code)


def fix_country(record: dict[str, str]) -> Optional[str]:
    country = clean_string(record["country"])
    if len(country) <= 3:
        return country.upper()
    return country.title()


def fix_stateprovince(record: dict[str, str]) -> Optional[str]:
    return clean_string(record["stateprovince"]).title()


def fix_county(record: dict[str, str]) -> Optional[str]:
    return clean_string(record["county"]).title()


def generic_fixer(field, str_func):
    def fixer(record: dict[str, str]):
        raw = record[field]
        return str_func(raw) if raw is not None else None
    return fixer


fixers = {
    "specificepithet": generic_fixer("specificepithet", str),
    "country": look_up_country_name_by_code,
    "stateprovince": fix_stateprovince,
    "county": fix_county,
}

for f in OUTPUT_FIELDS:
    if f not in fixers:
        fixers[f] = generic_fixer(f, str.title)


tsv_args: dict[str, Any] = dict(
    delimiter="\t",
    lineterminator="\n",
    escapechar="\\",
    quoting=csv.QUOTE_NONE
)

raw_records = csv.DictReader(sys.stdin, **tsv_args)

formatted_records = csv.DictWriter(sys.stdout, fieldnames=OUTPUT_FIELDS, **tsv_args)
formatted_records.writeheader()


for i, record in enumerate(raw_records):
    try:
        formatted_record = {f: fixers[f](record) for f in OUTPUT_FIELDS}
        if all((v for k, v in formatted_record.items())):
            formatted_records.writerow(formatted_record)
    except:
        print("HEREHRERHERE:", i, file=sys.stderr)
        print(record, file=sys.stderr)
        raise
