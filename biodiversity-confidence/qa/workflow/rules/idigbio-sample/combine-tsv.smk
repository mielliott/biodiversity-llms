checkpoint combine_presence_and_absence:
    input:
        presence=f"{inputs}/presence.tsv",
        absence=f"{inputs}/absence.tsv",
    output:
        f"{inputs}/all.tsv",
    shell:
        """
        mlr --tsvlite cat <(mlr --tsvlite put '$present = "Yes"' {input.presence})\
                          <(mlr --tsvlite put '$present = "No"' {input.absence})\
        > {output}
        """
