import io
from llm_io import IOHandler
from runner import ExperimentRunner
from tests import test_util


def test_runner():
    tsv = test_util.make_tsv_stream([{"x": "apple", "y": "orange"}, {"x": "horse", "y": "carriage"}])
    io_handler = IOHandler(
        ["just {x}", "{x} and {y}"],
        False,
        []
    )

    runner = ExperimentRunner("test", {}, io_handler)

    out_stream = io.StringIO()
    runner.run_experiment(tsv, out_stream)

    out_tsv = out_stream.getvalue()

    assert out_tsv == (
        "x\ty\tquery\tresponse\n"
        "apple\torange\tjust apple\tEchoing query \"just apple\"\n"
        "apple\torange\tapple and orange\tEchoing query \"apple and orange\"\n"
        "horse\tcarriage\tjust horse\tEchoing query \"just horse\"\n"
        "horse\tcarriage\thorse and carriage\tEchoing query \"horse and carriage\"\n"
    )
