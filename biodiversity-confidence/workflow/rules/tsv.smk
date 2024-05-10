checkpoint shuffle_tsv:
    input:
        "{file}.tsv"
    output:
        "{file}.tsv.shuffled"
    params:
        seed=config["random_seed"]
    shell:
        """
        mlr --tsvlite --seed {params.seed} shuffle {input} > {output}
        """
