def unescape(string):
    if '"' == string[0] == string[-1] or "'" == string[0] == string[-1]:
        return eval(string)
    else:
        return string

def get_queries(patterns, header, lines, do_unescape, filter=lambda x: True):
    fields = header.split("\t")

    for line in lines:
        line = line[:-1]
        values = line.split("\t")
        
        if do_unescape:
            values = [v for v in map(unescape, values)]
        
        for pattern in patterns:
            if filter(line):
                field_values = dict(zip(fields, values))
                yield (line, pattern.format(**field_values))

def batched(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)
