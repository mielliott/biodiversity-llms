import csv
import itertools
from typing import Any, Iterator, TextIO


class IOHandler:
    tsv_args: dict[str, Any] = dict(
        delimiter="\t",
        lineterminator="\n",
        escapechar="\\",
        quoting=csv.QUOTE_NONE
    )

    def __init__(self, patterns: list[str], unescape_input: bool, required_fields: list[str]):
        self.patterns = patterns
        self.unescape_input = unescape_input
        self.required_fields = required_fields

    def batched(self, iterable, n):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_queries(self, lines: TextIO) -> Iterator[dict]:
        for field_values in csv.DictReader(lines, None, **self.tsv_args):
            for pattern in self.patterns:
                yield field_values | {"query": pattern.format(**field_values)}

    def write_results(self, out_stream: TextIO, results: Iterator[dict]):
        first_result = next(results)
        missing_fields = {field for field in self.required_fields if field not in first_result}
        if missing_fields:
            raise RuntimeError("Missing output field(s): " + ", ".join(missing_fields))

        writer = csv.DictWriter(out_stream, first_result.keys(), **self.tsv_args)
        writer.writeheader()
        writer.writerows(itertools.chain([first_result], results))
