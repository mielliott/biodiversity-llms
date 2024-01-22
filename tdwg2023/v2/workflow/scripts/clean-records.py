import sys

def fix_country(country: str):
    if len(country) <= 3:
        return country.upper()
    else:
        return country.title()

fields = sys.stdin.readline().strip().split("\t")
print("\t".join(fields))

fixers = {
    "genus": str.capitalize,
    "country": fix_country,
    "stateprovince": str.title,
    "county": str.title
}

for line in sys.stdin.readlines():
    values = line.strip().split("\t")
    for i, field in enumerate(fields):
        if field in fixers:
            values[i] = fixers[field](values[i])
    print("\t".join(values), flush=True)
