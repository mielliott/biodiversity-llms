from args import TokenScoresFormat
from models.gpt import GPT


def test_gpt_3_5_first_token():
    gpt = GPT()
    gpt.set_parameters({"model_name": "gpt-3.5-turbo-0125", "scores": TokenScoresFormat.FIRST_TOKEN})
    results_stream = gpt.run(iter([
        {"x": "bear", "query": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "query": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["query"] == "What is the best kind of bear? Only say its name."
    assert result["question number"] == 0
    assert result["input token count"] == 20
    assert len(result["top tokens"]) == 5
    assert len(result["top tokens logprobs"]) == 5

    assert set(result.keys()) == {
        "x", "query", "responses", "question number", "top tokens", "top tokens logprobs", "input token count", "output token count"
    }

    result = results[1]
    assert result["x"] == "toad"
    assert result["query"] == "What is the best kind of toad? Only say its name."
    assert result["question number"] == 1
    assert result["input token count"] == 21
    assert len(result["top tokens"]) == 5
    assert len(result["top tokens logprobs"]) == 5

    assert set(result.keys()) == {
        "x", "query", "responses", "question number", "top tokens", "top tokens logprobs", "input token count", "output token count"
    }
