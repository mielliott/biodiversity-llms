## US & Mexico Maps

See [demo.ipynb](demo.ipynb)

Get counties and municipalities:

```bash
$ python3 maps/get_us_state_counties.py > maps/us_state_counties.tsv
$ python3 maps/get_mex_state_municipalities.py > maps/mex_state_municipalities.tsv
```

## US State Counties

Map out the distribution of _Acer saccharum_, the Sugar Maple.

```bash
$ cat maps/us_state_counties.tsv | sed 's/^/Acer\tsaccharum\t/' | cat <(echo "genus\tspecies\tstate\tcounty\tlat\lon") - > datasets/d3_us-honey-maple.tsv
```

```bash
$ cat maps/us_state_counties.tsv\
| pv --line-mode -ptl\
| python3 nlp/species-qa.py "Can Acer saccharum be found at {1}, {0}? Yes or no."\
> results/d3_gpt35.tsv
```

Reword it

```bash
$ cat datasets/us-state-counties.tsv\
| python3 nlp/species-qa.py "Does Acer saccharum naturally occur in {1}, {0}? Yes or no."\
| pv --line-mode -ptl\
> results/d3_gpt35_2.tsv
```

Use lat-lons instead of county names

```bash
$ cat datasets/us-state-counties.tsv\
| python3 nlp/species-qa.py "Does Acer saccharum naturally occur at latitude {2}, longitude {3}? Yes or no."\
| pv --line-mode -ptl\
> results/d3-acer-saccharum-latlon_gpt35.tsv
```

Use the common name

```bash
$ cat datasets/us-state-counties.tsv\
| python3 nlp/species-qa.py "Do sugar maples naturally occur at latitude {2}, longitude {3}? Yes or no."\
| pv --line-mode -ptl\
> results/d3-sugar-maple-latlon_gpt35.tsv
```

## Bees and flowers

Rafinesquia neomexicana

```bash
$ cat maps/us_state_counties.tsv maps/mex_state_municipalities.tsv\
| python3 nlp/species-qa.py "Does Rafinesquia neomexicana naturally occur in {1}, {0}? Yes or no."\
| pv --line-mode -ptl\
> results/state_muni_raf_neo.tsv

$ cat maps/us_state_counties.tsv maps/mex_state_municipalities.tsv\
| python3 nlp/species-qa.py "Does Rafinesquia neomexicana naturally occur at latitude {2}, longitude {3}? Yes or no."\
| pv --line-mode -ptl\
> results/lat_lon_raf_neo.tsv
```

```bash
$ cat maps/us_state_counties.tsv maps/mex_state_municipalities.tsv \
| python3 nlp/species-qa.py "Does Andrena olivacea naturally occur in {1}, {0}? Yes or no."\
> results/state_muni_and_oli.tsv\
&& cat maps/us_state_counties.tsv maps/mex_state_municipalities.tsv\
| python3 nlp/species-qa.py "Does Perdita malacothricis naturally occur in {1}, {0}? Yes or no."\
> results/state_muni_per_mal.tsv
```

Split results
```bash
$ head -n3110 results/state_muni_and_oli.tsv > results/us_admin_and_oli.tsv
$ cat <(echo -e "responses\tinput token count\toutput token count") <(tail -n +3112 results/state_muni_and_oli.tsv) > results/mex_admin_and_oli.tsv
```
