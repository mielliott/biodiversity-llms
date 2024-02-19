rule gather_binomials:
    input:
        "resources/records.zip"
    output:
        "results/input/taxa-species.tsv"
    shell:
        # unzip -p {input} | split -n r/1/5 | jq .indexTerms\
        """
        unzip -p {input} | jq .indexTerms\
        | mlr --ijson --otsv template -f "genus","specificepithet" --fill-with MISSING | grep -v MISSING\
        | mlr --tsv uniq -a\
        > {output}
        """

rule gather_taxa_for_upper_ranks:
    input:
        "resources/records.zip"
    output:
        "results/input/taxa-{rank}.tsv"
    shell:
        """
        unzip -p {input}\
        | jq .indexTerms\
        | jq "{{taxon: .{wildcards.rank}}}"\
        | mlr --ijson --otsv uniq -a\
        | grep -vE "^null$"\
        > {output}
        """
