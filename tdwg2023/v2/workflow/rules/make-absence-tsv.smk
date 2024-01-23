ABSENCE_IN_UNVALIDATED = ABSENCE_IN + ".unvalidated"

rule create_pseudo_absence_dataset:
    input:
        PRESENCE_IN
    output:
        temp(ABSENCE_IN_UNVALIDATED)
    params:
        shuffle_fields="'country','stateprovince','county'",
        seed=config["random_seed"]
    shell:
        """
        paste <(cat {input} | mlr --tsv cut -x -f {params.shuffle_fields})\
              <(cat {input} | mlr --tsv cut -f {params.shuffle_fields} | mlr --tsv --seed {params.seed} shuffle)\
        > {output}
        """

rule validate_absences:
    input:
        ABSENCE_IN_UNVALIDATED
    output:
        ABSENCE_VALID
    conda:
        "../envs/analysis.yml"
    script:
        "../scripts/validate-absences.py"

rule filter_absences:
    input:
        unvalidated=ABSENCE_IN_UNVALIDATED,
        validation=ABSENCE_VALID
    output:
        ABSENCE_IN
    shell:
        """
        paste <(cat {input.unvalidated})\
              <(cut -f2 {input.validation})\
        | mlr --tsvlite filter '$valid == "True"'\
        | mlr --tsvlite cut -xf "valid"\
        > {output}
        """
