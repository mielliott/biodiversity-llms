## Workflow execution examples

First activate a snakemake environment:

```bash
mamba create -n snakemake --file environment.yml
mamba activate snakemake
```

* Run taxonomy QA for GPT-3.5:

```bash
snakemake "results/idigbio-sample/gpt-3.5-turbo-0613/taxonomy/responses.tsv" --sdm "conda" -c 8 --configfile "config/idigbio-sample/gpt-3.5-turbo-0613.yml"
```

* Run US counties occurrence questions for GPT-4

```bash
snakemake "results/us-maps/gpt-4-1106-preview/occurrence/responses.tsv" --sdm "conda" -c 8 --configfile "config/us-maps/gpt-4-1106-preview.yml"
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
