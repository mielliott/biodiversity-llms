# rule analyze_results:
#     input:
#         taxonomy=f"results/{LLM}/taxonomy/responses.tsv"
#     output:
#         NOTEBOOK_OUT
#     params:
#         phrasings=lambda wildcards: config["qa"]["occurrence"]["query_templates"],
#         query_fields=config["qa"]["occurrence"]["query_fields"],
#         seed=config["results"]["random_seed"],
#         validate_absences=config["results"]["validate_absences"]
#     log:
#         notebook=NOTEBOOK_OUT
#     conda:
#         "../envs/analysis.yml"
#     notebook:
#         "../notebooks/" + config["results"]["notebook"]
