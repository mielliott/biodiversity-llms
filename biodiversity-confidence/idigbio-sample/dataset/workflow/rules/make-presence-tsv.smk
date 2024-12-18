from glob import glob


rule extract_records_as_tsv:
    input:
        manifest="results/manifest",
        records="results/records.zip",
    output:
        temp("results/records.tsv"),
    params:
        fields=",".join(
            [field for field in config["taxonomy_fields"] + config["location_fields"]]
        ),
    log:
        "logs/records.tsv",
    shell:
        """
        unzip -p {input.records}\
        | jq .indexTerms\
        | mlr --ijson --otsv template -f {params.fields}\
        | mlr --tsv uniq -a\
        1> {output} 2> {log}
        """


rule make_kingdom_presence_tsv:
    input:
        "results/records.tsv",
    output:
        temp("results/kingdom-{kingdom}.tsv"),
    log:
        "logs/kingdom-{kingdom}.tsv",
    conda:
        "../envs/download.yml"
    params:
        min_size=25,
        max_size=100,
        groupby="family",
        random_seed=config["random_seed"],
        num_records=10000,
    shell:
        """
        cat {input}\
        | mlr --tsv filter '$kingdom == "{wildcards.kingdom}"'\
        | python3 workflow/scripts/group_and_limit_records.py {params.groupby} {params.min_size} {params.max_size} {params.random_seed}\
        | mlr --tsv head -n {params.num_records}\
        1> {output} 2> {log}
        """


rule make_presence_tsv:
    input:
        "results/kingdom-animalia.tsv",
        "results/kingdom-plantae.tsv",
    output:
        "results/presence.tsv",
    log:
        "logs/presence.tsv",
    conda:
        "../envs/download.yml"
    shell:
        """
        mlr --tsv cat {input}\
        1> {output} 2> {log}
        """
