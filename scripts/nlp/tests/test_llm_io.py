import csv
import io
import pandas as pd
from llm_io import IOHandler
from tests import test_util


def test_query_generator():
    handler = IOHandler(["just {x}", "{x} and {y}"], False, [])

    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    query_gen = handler.make_queries(tsv)

    queries = list(query_gen)

    assert queries == [
        {"x": "apple", "y": "orange", "query": "just apple"},
        {"x": "apple", "y": "orange", "query": "apple and orange"},
        {"x": "horse", "y": "carriage", "query": "just horse"},
        {"x": "horse", "y": "carriage", "query": "horse and carriage"},
    ]


def test_read_output_tsv_with_pandas():
    handler = IOHandler([], False, [])

    out_stream = io.StringIO()
    handler.write_results(out_stream, iter([{
        "field 1": "value 1",
        "field 2": "value 2",
        "field 3": "value 3",
    }]))

    in_stream = io.StringIO(out_stream.getvalue())
    table = pd.read_csv(in_stream, sep="\t")

    assert len(table) == 1
    assert table.iloc[0].to_dict() == {
        "field 1": "value 1",
        "field 2": "value 2",
        "field 3": "value 3",
    }


def test_read_escaped_output_tsv_with_pandas():
    handler = IOHandler([], False, [])

    out_stream = io.StringIO()
    handler.write_results(out_stream, iter([{
        "field\t1": "value\t1",
        "field\n2": "value\n2",
        "field\r3": "value\r3",
    }]))

    in_stream = io.StringIO(out_stream.getvalue())
    table = pd.read_csv(in_stream, sep="\t", escapechar="\\", quoting=csv.QUOTE_NONE)

    assert len(table) == 1

    first_row = table.iloc[0].to_dict()
    assert first_row == {
        "field\t1": "value\t1",
        "field\n2": "value\n2",
        "field\r3": "value\r3",
    }
