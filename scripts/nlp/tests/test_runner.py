import io
import pytest
from llm_io import IOHandler
from runner import ExperimentRunner
from tests import test_util


def test_runner():
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(
        ["just {x}", "{x} and {y}"],
        []
    )

    runner = ExperimentRunner("test", {}, io_handler)

    out_stream = io.StringIO()
    runner.run_experiment(tsv, out_stream)

    out_tsv = out_stream.getvalue()

    assert out_tsv == (
        "x\ty\tquery\tresponse\n"
        "apple\torange\tjust apple\tEchoing query \\\"just apple\\\"\n"
        "apple\torange\tapple and orange\tEchoing query \\\"apple and orange\\\"\n"
        "horse\tcarriage\tjust horse\tEchoing query \\\"just horse\\\"\n"
        "horse\tcarriage\thorse and carriage\tEchoing query \\\"horse and carriage\\\"\n"
    )


def test_runner_with_disk_io():
    io_handler = IOHandler(
        ["Does species {genus} {specificepithet} live in {country}?"],
        []
    )

    runner = ExperimentRunner("test", {}, io_handler)

    out_stream = io.StringIO()

    with open("tests/resources/occurrence-qa.tsv", "r", encoding="utf-8") as f:
        runner.run_experiment(f, out_stream)

    out_tsv = out_stream.getvalue()

    assert out_tsv == (
        "genus\tspecificepithet\tcountry\tquery\tresponse\n"
        "Panicum\tlaxiflorum\tNepal\tDoes species Panicum laxiflorum live in Nepal?\tEchoing query \\\"Does species Panicum laxiflorum live in Nepal?\\\"\n"
        "Fenestella\tcarinata\tUganda\tDoes species Fenestella carinata live in Uganda?\tEchoing query \\\"Does species Fenestella carinata live in Uganda?\\\"\n"
    )


def test_runner_missing_required_fields():
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(
        ["just {x}", "{x} and {y}"],
        ["zorp"]
    )

    runner = ExperimentRunner("test", {}, io_handler)

    with pytest.raises(RuntimeError):
        out_stream = io.StringIO()
        runner.run_experiment(tsv, out_stream)
