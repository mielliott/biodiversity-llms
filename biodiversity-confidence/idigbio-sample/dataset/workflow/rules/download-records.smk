animalia_phyla = {
    "acanthocephala",
    "annelida",
    "arthropoda",
    "brachiopoda",
    "bryozoa",
    "chaetognatha",
    "chordata",
    "cnidaria",
    "ctenophora",
    "echinodermata",
    "entoprocta",
    "hemichordata",
    "mollusca",
    "nematoda",
    "nematomorpha",
    "nemertea",
    "onychophora",
    "phoronida",
    "platyhelminthes",
    "priapulida",
    "rotifera",
    "sipuncula",
    "tardigrada",
    "xenacoelomorpha",
}

plantae_phyla = {
    "tracheophyta",
    "bryophyta",
    "marchantiophyta",
    "rhodophyta",
    "chlorophyta",
    "charophyta",
    "anthocerotophyta",
}

records_per_family = 120
families_per_kingdom = len(plantae_phyla) * len(animalia_phyla)


rule get_animalia_records:
    output:
        "results/animalia.jsonl",
        "results/animalia.py.ipynb",
    params:
        records_per_family=records_per_family,
        families_per_kingdom=families_per_kingdom,
        kingdom="animalia",
        phyla=animalia_phyla,
        required_fields=config["record_fields"],
    log:
        notebook="results/animalia.py.ipynb",
    conda:
        "../envs/download.yml"
    notebook:
        "../notebooks/download.py.ipynb"


rule get_plantae_records:
    output:
        "results/plantae.jsonl",
        "results/plantae.py.ipynb",
    params:
        records_per_family=records_per_family,
        families_per_kingdom=families_per_kingdom,
        kingdom="plantae",
        phyla=plantae_phyla,
        required_fields=config["record_fields"],
    log:
        notebook="results/plantae.py.ipynb",
    conda:
        "../envs/download.yml"
    notebook:
        "../notebooks/download.py.ipynb"


rule zip_records:
    input:
        ancient("results/animalia.jsonl"),
        ancient("results/plantae.jsonl"),
    output:
        "results/records.zip",
    shell:
        """
        rm -f {output} &&\
        zip {output} {input}
        """


rule package_and_sign:
    input:
        "results/records.zip",
    output:
        "results/manifest",
    shell:
        """
        #!/bin/bash
        # Archive a copy of records.zip using its hash as the file name
        mkdir -p signed &&\
        cp results/records.zip signed/$(md5sum {input} | cut -c -32) &&\

        # Record the hash of the latest records.zip
        md5sum {input}\
        | sed "s/  /\t/"\
        | paste - <(date)\
        > {output} &&\

        # Concat the results to a persistent manifest
        cat {output} >> signed/manifest
        """
