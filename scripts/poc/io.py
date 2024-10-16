import sys

class IOHandler:
    def __init__(self):
        # parameters
        self.output = []
        self.input = []

        # Get header of input data
        sys.stdin.reconfigure(encoding='utf-8')
        self.lines = (line for line in sys.stdin)
        self.header = next(self.lines)[:-1]

    def unescape(self, string):
        if '"' == string[0] == string[-1] or "'" == string[0] == string[-1]:
            return eval(string)
        else:
            return string
        
    def generate_query(self, patterns, lines, do_unescape, filter=lambda x: True):
        fields = self.header.split("\t")
        lines = (l for l in self.lines)
        for line in lines:
            line = line[:-1]
            values = line.split("\t")
            
            if do_unescape:
                values = [v for v in map(self.unescape, values)]
            queries = []
            for pattern in patterns:
                if filter(line):
                    field_values = dict(zip(fields, values))
                    queries.append((line, pattern.format(**field_values)))
            return queries

    def record_input(self):
        pass
    def record_output(self):
        pass

    def to_tsv(self):
        # convert data to tsv 
        pass

    def show(self, results):
        write = lambda *args: print(*args, sep="\t")
        # Group results by input and query
        grouped_results = {}
        for result in results:
            key = (result['input'], result['query'])
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append(result)
        header = self.header.split("\t")
        header.extend(["query", "response number", "response", "question number", 
                "top tokens", "top tokens logprobs", "input token count", "output token count"])
        write(*header)
        
        for (input, query), group in grouped_results.items():
            for i, result in enumerate(group, 1):
                write(
                    input,
                    query,
                    i,
                    result['responses'],
                    result['question number'],
                    result['top tokens'],
                    result['top tokens logprobs'],
                    result['input token count'],
                    result['output token count']
                )
            print()

    def save_output(self):
        pass

    def save_input(self):
        pass

    def save(self):
        # save_output
        # save_input
        pass