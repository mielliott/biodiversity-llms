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
        "query_number\tpattern_number\tx\ty\tprompt\tresponses\n"
        "0\t0\tapple\torange\tjust apple\tEchoing query prompt \\\"just apple\\\"\n"
        "0\t1\tapple\torange\tapple and orange\tEchoing query prompt \\\"apple and orange\\\"\n"
        "1\t0\thorse\tcarriage\tjust horse\tEchoing query prompt \\\"just horse\\\"\n"
        "1\t1\thorse\tcarriage\thorse and carriage\tEchoing query prompt \\\"horse and carriage\\\"\n"
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
        "query_number\tpattern_number\tgenus\tspecificepithet\tcountry\tprompt\tresponses\n"
        "0\t0\tPanicum\tlaxiflorum\tNepal\tDoes species Panicum laxiflorum live in Nepal?\tEchoing query prompt \\\"Does species Panicum laxiflorum live in Nepal?\\\"\n"
        "1\t0\tFenestella\tcarinata\tUganda\tDoes species Fenestella carinata live in Uganda?\tEchoing query prompt \\\"Does species Fenestella carinata live in Uganda?\\\"\n"
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
