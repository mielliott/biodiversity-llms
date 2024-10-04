import sys

class IOHandling:
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
            
            for pattern in patterns:
                if filter(line):
                    field_values = dict(zip(fields, values))
                    yield (line, pattern.format(**field_values))

    def record_input(self):
        pass
    def record_output(self):
        pass

    def to_tsv(self):
        # convert data to tsv 
        pass

    def show(self, results): 
        # Process Result
        write = lambda *args: print(*args, sep="\t")
        for i, (input, output) in enumerate(results):
            # Print header on the first line
            if i == 0:
                write(self.header, *output.keys())
            # Print inputs and outputs
            write(input, *output.values())
        pass

    def save_output(self):
        pass

    def save_input(self):
        pass

    def save(self):
        # save_output
        # save_input
        pass