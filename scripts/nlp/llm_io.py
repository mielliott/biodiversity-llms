from typing import Any, Callable, Iterable, Iterator, TextIO


class TSVReader(Iterator):
    def __init__(self, lines: TextIO):
        self.lines = lines
        self.fields: list[str]

    def parse(self, line):
        return "\t".split(line)

    def __next__(self):
        if not self.fields:
            header = next(self.lines)
            self.fields = self.parse(header)

        line = next(self.lines)
        return (line, self.parse(line))


class TSVWriter:
    def __init__(self, input_fields: list[str]):
        self.input_fields = input_fields
        self.output_fields: list[str]

    def print(self, values: Iterable[Any]):
        return "\t".join(map(str, values))

    def write(self, data: dict[str, Any]):
        if not self.output_fields:
            self.output_fields = list(data.keys())
            self.print(self.input_fields + self.output_fields)

        self.print(data.values())


class IOHandler:
    def __init__(self, patterns: list[str], unescape_input: bool, required_output_fields: list[str], line_filter: Callable[[str], bool]):
        self.patterns = patterns
        self.unescape_input = unescape_input
        self.required_output_fields = required_output_fields
        self.line_filter = line_filter
        self.input_fields: list[str] = []
        self.reader: TSVReader

    def unescape(self, string):
        if '"' == string[0] == string[-1] or "'" == string[0] == string[-1]:
            return eval(string)
        return string

    def batched(self, iterable, n):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_query_generator(self, lines: TextIO) -> Iterator[tuple[str, str]]:
        self.reader = TSVReader(lines)

        for line, values in self.reader:
            if self.unescape_input:
                values = list(map(self.unescape, values))

            pattern_queries = []
            for pattern in self.patterns:
                if self.line_filter(line):
                    field_values = dict(zip(self.reader.fields, values))
                    pattern_queries.append((line, pattern.format(**field_values)))

            yield from pattern_queries

    def record_input(self):
        pass

    def record_output(self):
        pass

    def to_tsv(self):
        # convert data to tsv
        pass

    def show(self, results):
        writer = TSVWriter(self.reader.fields)

        for result in results:
            missing_fields = {field for field in result if field not in self.required_output_fields}
            if missing_fields:
                raise RuntimeError("Missing output field(s): " + ", ".join(missing_fields))

            writer.write(result)
