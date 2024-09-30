from glob import glob

# Can't just use `unzip -p` because it extracts files in different order than
# `unzip [in] -d [dir] & cat [dir]/*` which was used before automating things.
# If we end up submitting all queries for the gpt4 job, then order won't matter
# and we can simplify this
rule extract_records:
    input:
        f"resources/{JOB}/records.zip"
    output:
        directory(f"resources/{JOB}/records")
    shell:
        "unzip {input} -d {output}"

rule clean_records:
    input:
        folder=f"resources/{JOB}/records",
        files=glob(f"resources/{JOB}/records/*.jsonl")
    output:
        f"results/{JOB}/input/presence-unfiltered.tsv"
    params:
        fields=",".join([f'"{field}' for field in config["qa"]["occurrence"]["query_fields"]])
    log:
        "logs/clean_raws.log"
    shell:
        """
        cat {input.files:q}\
        | jq .indexTerms\
        | mlr --ijson --otsv template -f {params.fields} --fill-with MISSING\
        | grep -v MISSING\
        | mlr --tsv uniq -a\
        | python3 workflow/scripts/clean-records.py\
        1> {output} 2> {log}
        """

rule filter_raws_to_presence_tsv:
    input:
        f"results/{JOB}/input/presence-unfiltered.tsv"
    output:
        PRESENCE_IN
    script:
        "../scripts/filter-records.py"
