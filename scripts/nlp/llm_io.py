from typing import Any, Callable, Iterable, Iterator, TextIO


class TSVReader(Iterator):
    def __init__(self, lines: TextIO):
        self.lines = lines
        self.fields: list[str] = []

    def read(self):
        line = next(self.lines)
        return list(map(str.strip, line.split("\t")))

    def __next__(self):
        if not self.fields:
            self.fields = self.read()

        values = self.read()
        field_values = dict(zip(self.fields, values))
        return field_values


class TSVWriter:
    def __init__(self):
        self.output_fields: list[str]

    def print(self, values: Iterable[Any]):
        return "\t".join(map(str, values))

    def write(self, data: dict[str, Any]):
        if not self.output_fields:
            self.output_fields = list(data.keys())
            self.print(self.output_fields)

        self.print(data.values())


class IOHandler:
    def __init__(self, patterns: list[str], unescape_input: bool, required_output_fields: list[str]):
        self.patterns = patterns
        self.unescape_input = unescape_input
        self.required_output_fields = required_output_fields
        self.input_fields: list[str] = []
        self.reader: TSVReader

    def batched(self, iterable, n):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_query_generator(self, lines: TextIO) -> Iterator[tuple[str, str]]:
        self.reader = TSVReader(lines)

        for field_values in self.reader:
            for pattern in self.patterns:
                yield field_values | {"query": pattern.format(**field_values)}

    def record_input(self):
        pass

    def record_output(self):
        pass

    def to_tsv(self):
        # convert data to tsv
        pass

    def show(self, results):
        writer = TSVWriter()

        for result in results:
            missing_fields = {field for field in result if field not in self.required_output_fields}
            if missing_fields:
                raise RuntimeError("Missing output field(s): " + ", ".join(missing_fields))

            writer.write(result)
