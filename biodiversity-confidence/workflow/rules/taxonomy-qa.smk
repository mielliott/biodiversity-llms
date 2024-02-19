RANKS = [
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species"
]

BATCH_RESULTS_DIR = f"results/{LLM}/{str(QA_BATCH_SIZE)}"

rule gather_taxa:
    input:
        lambda _: [f"results/input/taxa-{rank}.tsv" for rank in RANKS]
    output:
        "results/input/taxa.tsv"
    shell:
        """
        cat {input} > {output}
        """
