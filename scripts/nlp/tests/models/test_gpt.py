
from models.gpt import GPT


def test_gpt_3_5():
    gpt = GPT()
    gpt.set_parameters({"model_name": "gpt-3.5-turbo-0125"})
    results_stream = gpt.run(iter([
        {"x": "bear", "query": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "query": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert results[0]["x"] == "bear"
    assert results[0]["query"] == "What is the best kind of bear? Only say its name."
    assert results[0]["responses"]
    assert results[0]["question number"] == 0
    assert results[0]["top tokens"]
    assert results[0]["top tokens logprobs"]
    assert results[0]["input token count"] == 20
    assert results[0]["output token count"]

    assert results[1]["x"] == "toad"
    assert results[1]["query"] == "What is the best kind of toad? Only say its name."
    assert results[1]["responses"]
    assert results[1]["question number"] == 1
    assert results[1]["top tokens"]
    assert results[1]["top tokens logprobs"]
    assert results[1]["input token count"] == 21
    assert results[1]["output token count"]
