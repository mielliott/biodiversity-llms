This is just a test [Snakemake](https://snakemake.github.io/) workflow to make sure things are set up to run in the bigger workflow.

## Running the workflow
Requirements:
- [Conda](https://www.anaconda.com/download) (for [Snakemake](https://snakemake.github.io/)). Note recommendations in https://snakemake.readthedocs.io/en/stable/getting_started/installation.html#installation-via-conda-mamba.

First create and activate the environment in `snakemake.yml`:

```sh
mamba env create -n snakemake -f ../snakemake.yml
mamba activate snakemake
```

Then run the workflow:

```sh
snakemake --cores 1 --configfile config/[CONFIG] --sdm conda
```

Where `[CONFIG]` is one of the YAML job descriptions located in the `config/` directory

Quick start:

```sh
mamba env create -n snakemake -f ../snakemake.yml
mamba activate snakemake
snakemake -c 1 --configfile config/free-response/gpt-3.5-turbo-0125.yml --sdm conda
```
