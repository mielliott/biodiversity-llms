import csv
import re
import sys
from typing import Any, Optional, cast
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
    return country.name if country is not None else None


def fix_countrycode(record: dict[str, str]) -> Optional[str]:
    code = clean_string(record["countrycode"])
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
        return str_func(record[field])
    return fixer


fixers = {
    "specificepithet": generic_fixer("specificepithet", str),
    "country": fix_country,
    "countrycode": fix_countrycode,
    "stateprovince": fix_stateprovince,
    "county": fix_county,
}

for f in set(OUTPUT_FIELDS) - set(fixers):
    fixers[f] = generic_fixer(f, str.title)


tsv_args: dict[str, Any] = dict(
    delimiter="\t",
    lineterminator="\n",
    escapechar="\\",
    quoting=csv.QUOTE_NONE
)

raw_records = csv.DictReader(sys.stdin, **tsv_args)
fields: list[str] = cast(list[str], raw_records.fieldnames)

cleaned_records = csv.DictWriter(sys.stdout, fieldnames=fields, **tsv_args)
cleaned_records.writeheader()


for record in raw_records:
    formatted_record = {f: fixers[f](record) for f in OUTPUT_FIELDS}
    if all((v is not None for k, v in formatted_record.items())):
        cleaned_records.writerow(record)
