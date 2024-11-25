rule get_preston:
    output:
        "resources/preston.jar",
    shell:
        """
        curl -L https://github.com/bio-guoda/preston/releases/download/0.7.17/preston.jar\
        > {output}
        """


rule get_records:
    input:
        "resources/preston.jar",
    output:
        f"{resources}/{{recordset_hash}}/records.zip",
    params:
        records_zip=config["recordset"],
        preston="java -jar resources/preston.jar",
        remotes=",".join(config["preston"]["remotes"]),
    shell:
        """
        {params.preston} get {params.records_zip} --remotes {params.remotes} --no-cache\
        > {output}; rm -r tmp
        """  # The tmp file is left by preston
