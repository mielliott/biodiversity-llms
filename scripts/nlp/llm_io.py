import csv
import itertools
from typing import Any, Generator, Iterable, Iterator, TextIO


class IOHandler:
    tsv_args: dict[str, Any] = dict(
        delimiter="\t",
        lineterminator="\n",
        escapechar="\\",
        quoting=csv.QUOTE_NONE
    )

    def __init__(self, patterns: list[str], required_fields: list[str]):
        self.required_fields = required_fields

        if len(patterns) > 0:
            self.query_preprocessor = QPExpandPatterns(patterns)
        else:
            self.query_preprocessor = QPPassthrough()

    def batched(self, iterable: Iterable[Any], n: int):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_queries(self, lines: TextIO) -> Iterator[dict[str, Any]]:
        for query_number, query in enumerate(csv.DictReader(lines, None, **self.tsv_args)):
            for expanded_query in self.query_preprocessor.expand(query):
                yield {"query_number": query_number} | expanded_query

    def write_results(self, out_stream: TextIO, results: Iterator[dict[str, Any]]):
        first_result = next(results)
        missing_fields = {field for field in self.required_fields if field not in first_result}
        if missing_fields:
            raise RuntimeError("Missing output field(s): " + ", ".join(missing_fields))

        writer = csv.DictWriter(out_stream, first_result.keys(), **self.tsv_args)
        writer.writeheader()
        writer.writerows(itertools.chain([first_result], results))


class QueryPreprocessor:
    def expand(self, query) -> Generator:
        raise NotImplementedError()


class QPPassthrough(QueryPreprocessor):
    def expand(self, query):
        yield query


class QPExpandPatterns(QueryPreprocessor):
    def __init__(self, patterns) -> None:
        self.patterns = patterns

    def expand(self, query):
        for pattern_number, pattern in enumerate(self.patterns):
            yield (
                {"pattern_number": pattern_number} |
                query |
                {"prompt": pattern.format(**query)}
            )
