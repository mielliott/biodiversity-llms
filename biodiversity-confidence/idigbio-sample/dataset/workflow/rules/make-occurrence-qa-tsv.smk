rule create_occ_qa_dataset:
    input:
        presence="results/presence.tsv",
        absence="results/absence.tsv",
    output:
        "results/occurrence-qa.tsv",
    log:
        "logs/absence.tsv.unvalidated.tsv",
    conda:
        "../envs/download.yml"
    params:
        output_fields=",".join(config["qa_fields"]),
    shell:
        """
        cat <(mlr --tsv filter '$occurrence = true' {input.presence})\
            <(mlr --tsv filter '$occurrence = false'  {input.absence})\
        | python3 workflow/scripts/format_records_for_qa.py {params.output_fields}\
        > {output}
        """
