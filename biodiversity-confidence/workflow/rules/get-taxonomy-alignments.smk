# TODO: use preston
rule get_nomer_report:
    output:
        "resources/names-aligned.tsv"
    params:
        records_zip=config["recordset"],
        preston="java -jar resources/preston.jar",
        remotes=",".join(config["preston"]["remotes"])
    shell:
        """
        curl -L https://raw.githubusercontent.com/mielliott/idigbio-sample-alignment/main/alignment-report/names-aligned.tsv\
         > {output}
        """

rule process_report:
    input:
        "resources/names-aligned.tsv"
    output:
        "results/input/alignments.tsv",
        "results/input/bad-names.tsv"
    script:
        "../scripts/taxonomy/process-nomer-report.py"
