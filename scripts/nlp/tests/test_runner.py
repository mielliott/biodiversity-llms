import csv
import io
import pytest
import pandas as pd
from args import Params
from llm_io import IOHandler
from runner import ExperimentRunner
from tests import test_util


def test_runner(capsys):
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(
        ["just {x}", "{x} and {y}"],
        []
    )

    runner = ExperimentRunner("test", Params("echo"), io_handler)
    runner.run_experiment(tsv)

    tsv, err = capsys.readouterr()

    assert tsv == (
        "x\ty\tquery_number\tpattern_number\tquery\tresponses\n"
        "apple\torange\t0\t0\tjust apple\tEchoing query \\\"just apple\\\"\n"
        "apple\torange\t0\t1\tapple and orange\tEchoing query \\\"apple and orange\\\"\n"
        "horse\tcarriage\t1\t0\tjust horse\tEchoing query \\\"just horse\\\"\n"
        "horse\tcarriage\t1\t1\thorse and carriage\tEchoing query \\\"horse and carriage\\\"\n"
    )


def test_runner_with_disk_io(capsys):
    io_handler = IOHandler(
        ["Does species {genus} {specificepithet} live in {country}?"],
        []
    )

    with open("tests/resources/occurrence-qa.tsv", "r", encoding="utf-8") as f:
        runner = ExperimentRunner("test", Params("echo"), io_handler)
        runner.run_experiment(f)

    tsv, err = capsys.readouterr()

    assert tsv == (
        "genus\tspecificepithet\tcountry\tquery_number\tpattern_number\tquery\tresponses\n"
        "Panicum\tlaxiflorum\tNepal\t0\t0\tDoes species Panicum laxiflorum live in Nepal?\tEchoing query \\\"Does species Panicum laxiflorum live in Nepal?\\\"\n"
        "Fenestella\tcarinata\tUganda\t1\t0\tDoes species Fenestella carinata live in Uganda?\tEchoing query \\\"Does species Fenestella carinata live in Uganda?\\\"\n"
    )


def test_runner_missing_required_fields():
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(
        ["just {x}", "{x} and {y}"],
        ["zorp"]
    )

    runner = ExperimentRunner("test", Params("echo"), io_handler)

    with pytest.raises(RuntimeError):
        runner.run_experiment(tsv)


def test_runner_gpt(capsys):
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(["just {x}", "{x} and {y}"], [])

    runner = ExperimentRunner("gpt", Params("gpt-3.5-turbo-0125"), io_handler)
    runner.run_experiment(tsv)

    tsv, err = capsys.readouterr()
    table = pd.read_csv(io.StringIO(tsv), sep="\t", escapechar="\\", quoting=csv.QUOTE_NONE)

    assert len(table) == 4


def test_runner_llama(capsys):
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(["just {x}", "{x} and {y}"], [])

    runner = ExperimentRunner("llama", Params("llama-3.1-8b"), io_handler)
    runner.run_experiment(tsv)

    tsv, err = capsys.readouterr()
    table = pd.read_csv(io.StringIO(tsv), sep="\t", escapechar="\\", quoting=csv.QUOTE_NONE)

    assert len(table) == 4
