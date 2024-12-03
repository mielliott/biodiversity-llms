# rule gather_binomials:  # Not used, it's a lot of questions and genus is present in binomial, so might as well only test on genus
#     input:
#         f"{resources}/{{recordset_hash}}/records.zip",
#     output:
#         f"{inputs}/taxa-species.tsv",
#     shell:
#         # unzip -p {input} | split -n r/1/5 | jq .indexTerms\
#         """
#         unzip -p {input} | jq .indexTerms\
#         | mlr --ijson --otsv template -f "genus","specificepithet" --fill-with MISSING | grep -v MISSING\
#         | mlr --tsv uniq -a\
#         > {output}
#         """


# RANKS = ["kingdom", "phylum", "class", "order", "family", "genus"]


# rule gather_taxa_for_upper_ranks:
#     input:
#         f"{resources}/{{recordset_hash}}/records.zip",
#     output:
#         f"{inputs}/taxa-{{rank}}.tsv",
#     params:
#         fields=",".join(RANKS + ["taxon"]),
#         higher_ranks=lambda wildcards: ",".join(RANKS[: RANKS.index(wildcards.rank)]),
#     shell:
#         """
#         unzip -p {input}\
#         | jq .indexTerms\
#         | jq "{{{params.higher_ranks}, taxon: .{wildcards.rank}}}"\
#         | mlr --ijson --otsv uniq -a\
#         | mlr --tsvlite template -f {params.fields} --fill-with ""\
#         | grep -vE "^null$"\
#         > {output}
#         """
# checkpoint make_taxonomy_questions:
#     input:
#         phylum=f"{inputs}/taxa-phylum.tsv",
#         class_=f"{inputs}/taxa-class.tsv",
#         order=f"{inputs}/taxa-order.tsv",
#         family=f"{inputs}/taxa-family.tsv",
#         genus=f"{inputs}/taxa-genus.tsv",
#     output:
#         f"{inputs}/taxonomy-qa.tsv",
#     params:
#         ranks=RANKS,
#     script:
#         "../scripts/make_taxonomy_qa_table.py"
