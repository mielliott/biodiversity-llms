rule get_kingdom_records:
    output:
        "results/{kingdom}.jsonl",
        "results/{kingdom}.py.ipynb",
    params:
        min_records_per_family=config["download"]["min_records_per_family"],
        max_records_per_family=config["download"]["max_records_per_family"],
        families_per_kingdom=config["download"]["families_per_kingdom"],
        kingdom=lambda wildcards: wildcards.kingdom,
        phyla=lambda wildcards: config["download"]["kingdoms"][wildcards.kingdom][
            "phyla"
        ],
        required_fields=config["record_fields"],
    log:
        notebook="results/{kingdom}.py.ipynb",
    conda:
        "../envs/download.yml"
    notebook:
        "../notebooks/download.py.ipynb"


rule zip_records:
    input:
        "results/animalia.jsonl",
        "results/plantae.jsonl",
    output:
        "results/records.zip",
    shell:
        """
        rm -f {output} &&\
        zip {output} {input}
        """
