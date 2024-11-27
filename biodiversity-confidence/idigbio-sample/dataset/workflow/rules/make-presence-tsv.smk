from glob import glob


rule make_presence_tsv:
    input:
        "results/records.zip",
    output:
        "results/presence.tsv",
    params:
        fields=",".join([f'"{field}"' for field in config["record_fields"]]),
    log:
        "logs/presence.tsv",
    shell:
        """
        unzip -p {input}\
        | jq .indexTerms\
        | mlr --ijson --otsv template -f {params.fields} --fill-with MISSING\
        | python3 workflow/scripts/clean_records.py\
        1> {output} 2> {log}
        """
        # """
        # unzip -p {input}\
        # | jq .indexTerms\
        # | mlr --ijson --otsv template -f {params.fields} --fill-with MISSING\
        # | grep -v MISSING\
        # | mlr --tsv uniq -a\
        # | python3 workflow/scripts/clean_records.py\
        # 1> {output} 2> {log}
        # """
