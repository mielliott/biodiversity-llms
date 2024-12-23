from math import ceil


def get_batches(namespace):
    batch_size = config["qa_batch_size"]
    num_lines = (
        sum(1 for line in open(config["qa_input"])) - 1
    )  # Don't count the header line

    limit = (
        num_lines
        if config["qa_query_limit"] <= 0
        else min(num_lines, config["qa_query_limit"])
    )

    return (
        get_batch_path(namespace, batch, batch_size, limit)
        for batch in range(ceil(limit / batch_size))
    )


def get_batch_path(namespace, batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"results/{namespace}/batches/{first}-{last}.tsv"
