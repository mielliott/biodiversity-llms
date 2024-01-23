rule create_pseudo_absence_dataset:
    input:
        PRESENCE_IN
    output:
        ABSENCE_IN
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
        ABSENCE_IN
    output:
        "results/absence-valid.tsv"
    conda:
        "../envs/analysis.yml"
    script:
        "../scripts/validate-absences.py"
