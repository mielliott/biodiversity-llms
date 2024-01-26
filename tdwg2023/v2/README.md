This repository contains a [Snakemake](https://snakemake.github.io/) workflow that performs the following:
1. Retrieves an occurrence records dataset ([10.5281/zenodo.8417751](https://zenodo.org/doi/10.5281/zenodo.8417751) / [hash://md5/8f0594be7f88e4fc7b30c0854e7ca029](https://linker.bio/hash://md5/8f0594be7f88e4fc7b30c0854e7ca029))
1. Generates a series of yes-or-no questions about the records
1. Submits the questions to an LLM (e.g., GPT3.5 or GPT4)
1. Analyzes the responses and trains a confidence model to predict thier correctness
1. Renders the results in a Jupyter notebook

## Running the workflow
Requirements:
- [Conda](https://www.anaconda.com/download) (for [Snakemake](https://snakemake.github.io/))
- Java 8+ (for [preston](https://preston.guoda.bio/))

First instantiate and activate the Conda environment described in `environment.yml`:

```sh
conda env create -n snakemake -f environment.yml
conda activate snakemake
```

Then run the workflow:

```sh
snakemake --cores 1 --configfile config/[CONFIG] --sdm conda
```

Where `[CONFIG]` is one of the YAML job descriptions located in the `config/` directory

Quick start:

This GPT3.5 workflow takes 1+ hours and costs ~$2.50 USD

```sh
mamba env create -n snakemake -f environment.yml
mamba activate snakemake
snakemake --cores 1 --configfile config/gpt-3.5-turbo-0613 --sdm conda
```