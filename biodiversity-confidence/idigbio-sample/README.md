The workflow takes a sample of iDigBio that is equally distributed across a hand-picked set of phyla. The phyla were selected from those listed at https://www.catalogueoflife.org/, only using those that have at least 1000 associated records in iDigBio.

* [Animalia record counts](https://beta-search.idigbio.org/v2/summary/top/records/?rq={"family":{"type":"exists"},"kingdom":"animalia"}&top_fields=["phylum"]&count=1000)
* [Plantae record counts](https://beta-search.idigbio.org/v2/summary/top/records/?rq={"family":{"type":"exists"},"kingdom":"plantae"}&top_fields=["phylum"]&count=1000)

To run:

```bash
mamba activate snakemake
snakemake
```

The workflow generates the following outputs:
```
results/
  animalia.jsonl 
  plantae.jsonl
  animalia.py.ipynb
  plantae.py.ipynb
  presence.tsv
  records.zip
```

TODO: Zip it all up
