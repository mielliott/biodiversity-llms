# rule create_pseudo_absence_dataset:
#     input:
#         f"results/presence.tsv",
#     output:
#         temp(f"results/absence.tsv.unvalidated"),
#     params:
#         shuffle_fields="'country','stateprovince','county'",
#         seed=config["random_seed"],
#     shell:
#         """
#         paste <(cat {input} | mlr --tsv cut -x -f {params.shuffle_fields})\
#               <(cat {input} | mlr --tsv cut -f {params.shuffle_fields} | mlr --tsv --seed {params.seed} shuffle)\
#         > {output}
#         """


# rule validate_absences:
#     input:
#         f"results/absence.tsv.unvalidated",
#     output:
#         protected(f"results/absence-valid.tsv"),
#     conda:
#         "../envs/analysis.yml"
#     script:
#         "../scripts/validate_absences.py"
# rule filter_absences:
#     input:
#         unvalidated=f"results/absence.tsv.unvalidated",
#         validation=ancient(f"results/absence-valid.tsv"),
#     output:
#         f"results/absence.tsv",
#     shell:
#         """
#         paste <(cat {input.unvalidated})\
#               <(cut -f2 {input.validation})\
#         | mlr --tsvlite filter '$valid == "True"'\
#         | mlr --tsvlite cut -xf "valid"\
#         > {output}
#         """
