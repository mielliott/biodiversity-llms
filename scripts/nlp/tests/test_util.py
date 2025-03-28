import io
from types import SimpleNamespace
from typing import Any


def mock_static(**attributes):
    def supplier(*args, **kwargs):
        return SimpleNamespace(**attributes)
    return supplier


def make_tsv_stream(data: list[dict[str, Any]]) -> io.StringIO:
    header = "\t".join(data[0].keys())
    rows = "\n".join(["\t".join(x.values()) for x in data])

    return io.StringIO(header + "\n" + rows + "\n")


def test_make_tsv_stream():
    data = [
        {"name": "Marge", "job": "trucker"},
        {"name": "Louis", "job": "trumpet"}
    ]

    tsv = make_tsv_stream(data).getvalue()

    assert tsv == (
        "name\tjob\n"
        "Marge\ttrucker\n"
        "Louis\ttrumpet\n"
    )
