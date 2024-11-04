from glob import glob


rule clean_records:
    input:
        f"resources/{JOB}/records.zip",
    output:
        f"results/{JOB}/input/presence-unfiltered.tsv",
    params:
        fields=",".join(
            [f'"{field}' for field in config["qa"]["occurrence"]["query_fields"]]
        ),
    log:
        "logs/clean_raws.log",
    shell:
        """
        unzip -p {input}\
        | jq .indexTerms\
        | mlr --ijson --otsv template -f {params.fields} --fill-with MISSING\
        | grep -v MISSING\
        | mlr --tsv uniq -a\
        | python3 workflow/scripts/clean-records.py\
        1> {output} 2> {log}
        """


rule filter_raws_to_presence_tsv:
    input:
        f"results/{JOB}/input/presence-unfiltered.tsv",
    output:
        PRESENCE_IN,
    script:
        "../scripts/filter-records.py"
