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
        "download.py.ipynb"


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
        "download.py.ipynb"


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
