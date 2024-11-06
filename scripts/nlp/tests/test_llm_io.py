import io
from llm_io import IOHandler, TSVReader


def make_io(*args: str):
    return io.StringIO("\n".join(args) + "\n")


def test_tsv_reader():
    tsv = [
        "a\tb",
        "1\t2",
        "3\t4"
    ]

    reader = TSVReader(make_io(*tsv))

    data = list(reader)

    assert data == [
        {"a": "1", "b": "2"},
        {"a": "3", "b": "4"}
    ]


def test_query_generator():
    handler = IOHandler(["just {x}", "{x} and {y}"], False, [])

    query_gen = handler.make_query_generator(
        make_io("x\ty", "apple\torange", "horse\tcarriage"),
    )

    queries = list(query_gen)

    assert queries == [
        {"x": "apple", "y": "orange", "query": "just apple"},
        {"x": "apple", "y": "orange", "query": "apple and orange"},
        {"x": "horse", "y": "carriage", "query": "just horse"},
        {"x": "horse", "y": "carriage", "query": "horse and carriage"},
    ]
