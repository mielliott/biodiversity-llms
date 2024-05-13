# TODO: use preston
rule get_nomer_report:
    output:
        f"resources/{JOB}/names-aligned.tsv"
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
        f"resources/{JOB}/names-aligned.tsv"
    output:
        f"results/{JOB}/input/alignments.tsv",
        f"results/{JOB}/input/bad-names.tsv"
    script:
        "../scripts/taxonomy/process-nomer-report.py"
