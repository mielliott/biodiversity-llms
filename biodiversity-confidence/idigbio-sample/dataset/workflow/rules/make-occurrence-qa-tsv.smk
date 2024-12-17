rule create_occ_qa_dataset:
    input:
        presence="results/presence.tsv",
        absence="results/absence.tsv",
    output:
        "results/occurrence-qa.tsv",
    log:
        "logs/absence.tsv.unvalidated.tsv",
    shell:
        """
        cat <(mlr --tsv filter '$answer = "yes"' {input.presence})\
            <(mlr --tsv filter '$answer = "no"'  {input.absence})\
        | python3 workflow/scripts/format_records_for_qa.py\
        > {output}
        """
