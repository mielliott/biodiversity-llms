import csv
import itertools
from typing import Any, Iterable, Iterator, TextIO


class IOHandler:
    tsv_args: dict[str, Any] = dict(
        delimiter="\t",
        lineterminator="\n",
        escapechar="\\",
        quoting=csv.QUOTE_NONE
    )

    def __init__(self, patterns: list[str], required_fields: list[str]):
        self.patterns = patterns
        self.required_fields = required_fields

    def batched(self, iterable: Iterable[Any], n: int):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_queries(self, lines: TextIO) -> Iterator[dict[str, Any]]:
        for query_number, field_values in enumerate(csv.DictReader(lines, None, **self.tsv_args)):
            for pattern_number, pattern in enumerate(self.patterns):
                yield field_values | {
                    "query_number": query_number,
                    "pattern_number": pattern_number,
                    "prompt": pattern.format(**field_values)
                }

    def write_results(self, out_stream: TextIO, results: Iterator[dict[str, Any]]):
        first_result = next(results)
        missing_fields = {field for field in self.required_fields if field not in first_result}
        if missing_fields:
            raise RuntimeError("Missing output field(s): " + ", ".join(missing_fields))

        writer = csv.DictWriter(out_stream, first_result.keys(), **self.tsv_args)
        writer.writeheader()
        writer.writerows(itertools.chain([first_result], results))
