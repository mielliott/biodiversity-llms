# TODO: use preston
rule get_nomer_report:
    output:
        f"{resources}/names-aligned.tsv",
    params:
        records_zip=config["recordset"],
        preston="java -jar resources/preston.jar",
        remotes=",".join(config["preston"]["remotes"]),
        report_url=config["nomer_alignment_report_url"],
    shell:
        """
        curl -L {params.report_url}\
         > {output}
        """


rule process_report:
    input:
        f"{resources}/names-aligned.tsv",
    output:
        f"{inputs}/alignments.tsv",
        f"{inputs}/bad-names.tsv",
    script:
        "../scripts/taxonomy/process_nomer_report.py"
