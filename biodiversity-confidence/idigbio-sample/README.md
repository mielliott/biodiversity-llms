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
  animalia.py.ipynb # Documents the download process for animalia records
  plantae.py.ipynb  # Documents the download process for plantae records
  records.zip       # Contains animalia and plantae records in jsonl files
  occurrence-qa.tsv # Parameters for species presence and absence Q&A
```
