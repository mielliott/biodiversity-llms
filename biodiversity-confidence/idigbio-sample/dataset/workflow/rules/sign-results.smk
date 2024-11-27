rule package_and_sign:
    input:
        "results/records.zip",
    output:
        "results/manifest",
    shell:
        """
        #!/bin/bash
        # Archive a copy of records.zip using its hash as the file name
        mkdir -p signed &&\
        cp results/records.zip signed/$(md5sum {input} | cut -c -32) &&\

        # Record the hash of the latest records.zip
        md5sum {input}\
        | sed "s/  /\t/"\
        | paste - <(date)\
        > {output} &&\

        # Concat the results to a persistent manifest
        cat {output} >> signed/manifest
        """


# rule package_as_zip:
#     input:
#         ancient("results/animalia.jsonl"),
#         ancient("results/plantae.jsonl"),
#         "resources/preston.jar",
#     output:
#         "results/manifest",
#     shell:
#         """
#         preston track {input} &&\
#         preston alias --log tsv\
#         > {output}
#         """
# rule get_preston:
#     output:
#         "resources/preston.jar",
#     shell:
#         """
#         curl -L https://github.com/bio-guoda/preston/releases/download/0.10.0/preston.jar\
#         > {output}
#         """
# rule get_records:
#     input:
#         "resources/preston.jar",
#     output:
#         f"{resources}/{{recordset_hash}}/records.zip",
#     params:
#         records_zip=config["recordset"],
#         preston="java -jar resources/preston.jar",
#         remotes=",".join(config["preston"]["remotes"]),
#     shell:
#         """
#         {params.preston} get {params.records_zip} --remotes {params.remotes} --no-cache\
#         > {output}; rm -r tmp
#         """  # The tmp file is left by preston
