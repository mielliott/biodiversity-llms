rule create_occ_qa_dataset:
    input:
        presence="results/presence.tsv",
        absence="results/absence.tsv",
    output:
        "results/occurrence-qa.tsv",
    log:
        "logs/occurrence-qa.tsv",
    conda:
        "../envs/download.yml"
    params:
        output_fields=",".join(config["qa_fields"]),
    shell:
        """
        mlr --tsv cat <(mlr --tsv put '$occurrence = true'  {input.presence})\
                      <(mlr --tsv put '$occurrence = false' {input.absence})\
        | python3 workflow/scripts/format_records_for_qa.py {params.output_fields}\
        | mlr --tsv put '$query_number = NR - 1'\
        | mlr --tsv reorder -f query_number\
        > {output}
        """
