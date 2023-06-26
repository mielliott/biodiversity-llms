
Get the latest preston crawl log from https://linker.bio:

```bash
$ preston head --remote https://linker.bio
hash://sha256/c5989d88250fd6c92f312dd01afa52126b7f02f29d639306a912da088c4e1d3f
```

Get URLs and hashes of tracked DWC archives:

```bash
$ preston get --remote https://linker.bio hash://sha256/c5989d88250fd6c92f312dd01afa52126b7f02f29d639306a912da088c4e1d3f > 2023-06-01.nq
$ sparql --data=2023-06-01.nq -query=get-dwcas.rq --results=tsv > dwcaurl-versions
```

The output is a TSV list where the first row contains column headers and the rest contain (URL, hash) pairs:

```bash
$ head dwcaurl-versions
?url    ?version
<https://collections.nmnh.si.edu/ipt/archive.do?r=prytanomyia>  <hash://sha256/24db74f5c0b2eeb1022ec6274dc1713386c80aa007835307dc96c6b1ab3fcc35>
<https://collections.nmnh.si.edu/ipt/archive.do?r=plyomydas>    <hash://sha256/2b4bbbd575e109a30801e182fa5933a0574d9f5796eba58ecaaddb87fce7ea1b>
<https://collections.nmnh.si.edu/ipt/archive.do?r=nmnh_material_sample> <hash://sha256/60e315cb5aa07976510db3f96f6e9e859018428a042c7dcfe471296db6c45699>
<https://collections.nmnh.si.edu/ipt/archive.do?r=afrotropical_mydidae> <hash://sha256/14a8bc64c8b2ab06b2229bd1d2bd0e30c64d4ba794ead82438b2b4848e207fb6>
<https://collections.nmnh.si.edu/ipt/archive.do?r=eremohaplomydas>      <hash://sha256/596393a651231a367b4f34655ec172a0bb4e201f65772ddb744875f1b6dffeea>
<https://collections.nmnh.si.edu/ipt/archive.do?r=asiloid-flies>        <hash://sha256/089c7971ca68c6061c22ffc2fa2c19dfa0188ea0946c2a9cbef083bbad02b1be>
<https://collections.nmnh.si.edu/ipt/archive.do?r=nmnh_occurrence_archive>      <hash://sha256/0095d0c426ad1efc5eaa840070552d0be29ff0603e092d99206a55cc410e0994>
<https://collections.nmnh.si.edu/ipt/archive.do?r=nmnh_paleo_dwc-a>     <hash://sha256/376e33d6fc1d6c493c86a1160a5d2f835710737d92f649c947a386715bd480a4>
<https://collections.nmnh.si.edu/ipt/archive.do?r=anasillomos>  <hash://sha256/96f118f2ae0c83248595738531fd676ad10e558b315fefb6f1f33b92aa2adb12>
```

Get all the records:

```bash
$ tail dwcaurl-versions -n+2\
| awk '{print $1 " <http://purl.org/pav/hasVersion> " $2 " ."}'\
| preston dwc-stream --remote https://linker.bio\
> idigbio.jsonl
```

Or don't - it explodes - so just get the first 10,000 or so:

```bash
$ tail dwcaurl-versions -n+2\
| awk '{print $1 " <http://purl.org/pav/hasVersion> " $2 " ."}'\
| preston dwc-stream\
| jq '{"http://rs.tdwg.org/dwc/terms/genus", "http://rs.tdwg.org/dwc/terms/specificEpithet", "http://rs.tdwg.org/dwc/terms/country", "http://rs.tdwg.org/dwc/terms/stateProvince"}'\
| mlr --j2t cat\
| grep -v "null"\
| grep -v "sp."\
| head -n10000\
| sort -u\
> genus-epithet-country-province-10000.tsv
```

Get an LLM's responses to occurrence quesstions (using flan-T5-xxl, 11B):

```bash
$ cat datasets/d1_genus-epithet-country-province-10000.tsv\
| pv --line-mode -ptl\
| python3 ~/nlp/species-qa.py\
> results/d1_flan-t5-xxl.tsv
```

6,668 total questions:

| Flan-T5-XXL | D1   | D2   | D2(2)
|-------------|------|------|------
| Yes         | 5187 | 4790 | 5142
| No          | 1481 | 1878 | 1526


| GPT-3.5-turbo | D1   | D2
|---------------|------|-----
| Yes           | 3321 | 1343
| No            | 1257 | 3273  
| Maybe         | 1961 | 1962  
| Abstain       | 129  | 90 

```bash
$ tail -n+2 results/d1_gpt35.tsv | cut -f1 | grep -v No | grep Yes | wc -l
3321
$ tail -n+2 results/d1_gpt35.tsv | cut -f1 | grep No | grep -v Yes | wc -l
1257
$ tail -n+2 results/d1_gpt35.tsv | cut -f1 | grep No | grep Yes | wc -l
1961
$ expr 6668 - 3321 - 1257 - 1961
129
```

```bash
$ tail -n+2 results/d2_gpt35.tsv | cut -f1 | grep -v No | grep Yes | wc -l
1343
$ tail -n+2 results/d2_gpt35.tsv | cut -f1 | grep No | grep -v Yes | wc -l
3273
$ tail -n+2 results/d2_gpt35.tsv | cut -f1 | grep No | grep Yes | wc -l
1962
$ expr 6668 - 1343 - 3273 - 1962
90
```
