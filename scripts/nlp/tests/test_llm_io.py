import io
from llm_io import IOHandler, TSVReader, TSVWriter
from tests import test_util


def test_tsv_reader():
    tsv = (
        "a\tb\n"
        "1\t2\n"
        "3\t4\n"
    )

    reader = TSVReader(io.StringIO(tsv))

    data = list(reader)

    assert data == [
        {"a": "1", "b": "2"},
        {"a": "3", "b": "4"}
    ]


def test_tsv_writer():
    data = [
        {"a": "1", "b": "2"},
        {"a": "3", "b": "4"}
    ]

    out_stream = io.StringIO()
    writer = TSVWriter(out_stream)

    for obj in data:
        writer.write(obj)

    tsv = out_stream.getvalue()

    assert tsv == (
        "a\tb\n"
        "1\t2\n"
        "3\t4\n"
    )


def test_query_generator():
    handler = IOHandler(["just {x}", "{x} and {y}"], False, [])

    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    query_gen = handler.make_query_reader(tsv)

    queries = list(query_gen)

    assert queries == [
        {"x": "apple", "y": "orange", "query": "just apple"},
        {"x": "apple", "y": "orange", "query": "apple and orange"},
        {"x": "horse", "y": "carriage", "query": "just horse"},
        {"x": "horse", "y": "carriage", "query": "horse and carriage"},
    ]