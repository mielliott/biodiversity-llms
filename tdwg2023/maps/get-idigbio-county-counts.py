import sys
import requests as rq
import json
import time

def get_county_name_variations(verbatim):
    return set((verbatim, verbatim.split()[0]))

if __name__ == '__main__':
    # lines = (line for line in open("/home/mielliott/tdwg2023/idigbio/d1_genus-epithet-country-province-10000.tsv", "rt", encoding="utf-8"))
    sys.stdin.reconfigure(encoding='utf-8')
    lines = (line for line in sys.stdin)
    next(lines) # skip header line
    
    if len(sys.argv) > 1:
        genus, epithet = " ".join(sys.argv[1:]).split()[:2]
    else:
        raise Exception("Missing [genus] [specific epithet] arguments")

    for line in lines:
        state, county = line.split("\t")[:2]

        count = 0
        for county_name in get_county_name_variations(county):
            while (True):
                req = ("https://search.idigbio.org/v2/search/records?rq={"
                    f"\"genus\":\"{genus}\","
                    f"\"specificepithet\":\"{epithet}\","
                    f"\"county\":\"{county}\","
                    f"\"stateprovince\":\"{state}\""
                    "}")
                res = rq.get(req)
                if res.status_code == 200:
                    break
                else:
                    print(f"Request failed: {req}\nWaiting 5 seconds", file=sys.stderr, flush=True)
                    time.sleep(5)

            count += json.loads(res.content)["itemCount"]
        
        print(state, county, count, sep="\t", flush=True)
