import sys
from collections import defaultdict
from typing import Callable, Iterator

class IOHandler:
    def __init__(self, patterns: list[str], unescape_input: bool, line_filter: Callable[[str], bool]):
        self.patterns = patterns
        self.unescape_input = unescape_input
        self.line_filter = line_filter
        
        sys.stdin.reconfigure(encoding='utf-8')
        self.lines = (line for line in sys.stdin)

        # Get header of input data
        self.header = next(self.lines)[:-1]

    def unescape(self, string):
        if '"' == string[0] == string[-1] or "'" == string[0] == string[-1]:
            return eval(string)
        else:
            return string

    def batched(self, iterable, n):
        args = [iter(iterable)] * n
        return zip(*args)

    def make_query_generator(self) -> Iterator[tuple[str, str]]:
        fields = self.header.split("\t")
        
        for line in self.lines:
            line = line[:-1]
            values = line.split("\t")
            
            if self.unescape_input:
                values = list(map(self.unescape, values))

            pattern_queries = []
            for pattern in self.patterns:
                if self.line_filter(line):
                    field_values = dict(zip(fields, values))
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
        write = lambda *args: print(*args, sep="\t")
        header = self.header.split("\t") + [
            "query", "response", "question number", 
            "top tokens", "top tokens logprobs", 
            "input token count", "output token count"
        ]
        write(*header)
        
        # Group results by (input, query)
        grouped_results = defaultdict(list)
        for result in results:
            key = (result['input'], result['query'])
            grouped_results[key].append(result)
        
        for (input_line, query), group in grouped_results.items():
            for result in group:
                row = [
                    input_line,
                    query,
                    result['responses'],
                    result['question number'],
                    result['top tokens'],
                    result['top tokens logprobs'],
                    result['input token count'],
                    result['output token count']
                ]
                write(*row)

    def save_output(self):
        pass

    def save_input(self):
        pass

    def save(self):
        # save_output
        # save_input
        pass
