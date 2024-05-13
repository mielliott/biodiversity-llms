## Workflow execution examples

First activate the conda environment:

```bash
mamba activate snakemake
```

* Run taxonomy QA for GPT-3.5:

```bash
snakemake "results/idigbio-sample/gpt-3.5-turbo-0613/taxonomy/responses.tsv" --sdm "conda" -c 8 --configfile "config/gpt-3.5-turbo-0613.yml"
```

## Future work

* Improve taxonomy QA
    * Questions should probably specify the kingdom, as names can be reused across kingdoms
    * Fungi sets are currently unusable for various reasons
    * Names that nomer failed to align:
        * Athrostichtus
        * Bombus pyrobombus
        * Bombus subterraneobombus
        * Eucera xenoglossa
        * Indet
        * Melissodes eumelissodes
        * Ophiocrosota
        * Phyllocaenia
        * Towndsendia
        * X serapicamptis
        * scientificName
