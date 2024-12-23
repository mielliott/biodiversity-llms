rule package_and_sign:
    input:
        records="results/records.zip",
        occurrence_qa="results/occurrence-qa.tsv",
    output:
        "results/manifest",
    shell:
        """
        #!/bin/bash
        # Archive a the inputs using their hashes as file names
        mkdir -p signed &&\
        cp {input.records} signed/$(md5sum {input.records} | cut -c -32) &&\
        cp {input.occurrence_qa} signed/$(md5sum {input.occurrence_qa} | cut -c -32) &&\

        # Record the hash of records.zip
        md5sum {input.records}\
        | sed "s/  /\t/"\
        | paste - <(date)\
        > {output} &&\

        # Record the hash of occurrence-qa.tsv
        md5sum {input.occurrence_qa}\
        | sed "s/  /\t/"\
        | paste - <(date)\
        >> {output} &&\

        # Concat the results to a persistent manifest
        cat {output} >> signed/manifest
        """
