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
        required_fields=config["taxonomy_fields"] + config["location_fields"],
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
