checkpoint combine_presence_and_absence:
    input:
        presence="results/presence.tsv",
        absence="results/absence.tsv",
    output:
        "results/all.tsv",
    shell:
        """
        mlr --tsvlite cat <(mlr --tsvlite put '$present = "Yes"' {input.presence})\
                          <(mlr --tsvlite put '$present = "No"' {input.absence})\
        > {output}
        """
