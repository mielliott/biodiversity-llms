checkpoint shuffle_tsv:
    input:
        "{file}.tsv",
    output:
        f"{{file}}-shuffled-{config['random_seed']}.tsv",
    params:
        seed=config["random_seed"],
    shell:
        """
        mlr --tsvlite --seed {params.seed} shuffle {input} > {output}
        """
