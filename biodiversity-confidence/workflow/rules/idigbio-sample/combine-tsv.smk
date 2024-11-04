checkpoint combine_presence_and_absence:
    input:
        presence=PRESENCE_IN,
        absence=ABSENCE_IN,
    output:
        ALL_IN_UNSHUFFLED,
    shell:
        """
        mlr --tsvlite cat <(mlr --tsvlite put '$present = "Yes"' {input.presence})\
                          <(mlr --tsvlite put '$present = "No"' {input.absence})\
        > {output}
        """
