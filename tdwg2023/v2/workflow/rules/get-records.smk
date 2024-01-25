rule get_preston:
    output:
        "resources/preston.jar"
    shell:
        """
        curl -L https://github.com/bio-guoda/preston/releases/download/0.7.17/preston.jar\
        > {output}
        """

rule get_records:
    input:
        "resources/preston.jar"
    output:
        "resources/records.zip"
    params:
        records_zip="hash://md5/8f0594be7f88e4fc7b30c0854e7ca029",
        preston="java -jar resources/preston.jar",
        remotes="https://zenodo.org,https://linker.bio"
    shell:
        """
        {params.preston} get {params.records_zip} --remotes {params.remotes} --no-cache\
        > {output}; rm -r tmp
        """ # The tmp file is left by preston
