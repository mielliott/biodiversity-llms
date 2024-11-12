from glob import glob


rule clean_records:
    input:
        f"{resources}/records.zip",
    output:
        f"{inputs}/presence-unfiltered.tsv",
    params:
        fields=",".join(
            [f'"{field}"' for field in config["qa"]["occurrence"]["query_fields"]]
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
        | python3 workflow/scripts/clean_records.py\
        1> {output} 2> {log}
        """


rule filter_raws_to_presence_tsv:
    input:
        f"{inputs}/presence-unfiltered.tsv",
    output:
        f"{inputs}/presence.tsv",
    script:
        "../../scripts/filter_records.py"
