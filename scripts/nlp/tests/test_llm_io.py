import io
from llm_io import IOHandler


def list_as_io(lines: list[str]):
    return io.StringIO("\n".join(lines) + "\n")


def test_query_generator():
    handler = IOHandler(
        [
            "just {x}",
            "{x} and {y}"
        ],
        False,
        lambda query: "horse" not in query
    )

    query_gen = handler.make_query_generator(
        list_as_io(["x\ty", "apple\torange", "horse\tcarriage", "1\t2"]),
    )

    queries = list(query_gen)

    assert queries == [
        ('apple\torange', 'just apple'),
        ('apple\torange', 'apple and orange'),
        ('1\t2', 'just 1'),
        ('1\t2', '1 and 2')
    ]
