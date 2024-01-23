rule combine_presence_and_absence:
    input:
        presence=PRESENCE_IN,
        absence=ABSENCE_IN,
    output:
        ALL_IN
    shell:
        """
        cat <(cat {input.presence} | mlr --tsvlite put '$present = "Yes"')\
            <(cat {input.absence} | mlr --tsvlite put '$present = "No"')\
        > {output}
        """
