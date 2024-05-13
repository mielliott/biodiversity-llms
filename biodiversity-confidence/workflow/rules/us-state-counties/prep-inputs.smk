rule usqa_prep_inputs:
    input:
        f"resources/{JOB}/us-state-counties.tsv"
    output:
        f"results/{JOB}/input/acer-saccharum.tsv"
    script:
        """
        cat {input}\
        | mlr --tsvlite put '$kingdom="plantae"; $phylum="tracheophyta"; $class="magnoliopsida"; $order="sapindales"; $family="sapindaceae"; $genus="Acer"; $specificepithet="saccharum"'\
        > {output}
        """
