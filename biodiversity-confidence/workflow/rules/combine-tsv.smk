checkpoint combine_presence_and_absence:
    input:
        presence=PRESENCE_IN,
        absence=ABSENCE_IN,
    output:
        ALL_IN
    shell:
        """
        mlr --tsvlite cat <(mlr --tsvlite put '$present = "Yes"' {input.presence})\
                          <(mlr --tsvlite put '$present = "No"' {input.absence})\
        > {output}
        """

rule shuffle_presence_and_absence:
    input:
        ALL_IN
    output:
        ALL_IN_SHUFFLED
    params:
        seed=config["random_seed"]
    shell:
        """
        mlr --tsvlite --seed {params.seed} shuffle {input} > {output}
        """