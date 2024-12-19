from args import Params
from models.dummy import Test


def test_echo():
    gpt = Test(Params(model_name="echo"))
    results_stream = gpt.run(iter([
        {"x": "bear", "prompt": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "prompt": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["prompt"] == "What is the best kind of bear? Only say its name."
    assert result["responses"] == "Echoing query \"What is the best kind of bear? Only say its name.\""

    assert set(result.keys()) == {
        "x", "prompt", "responses"
    }

    result = results[1]
    assert result["x"] == "toad"
    assert result["responses"] == "Echoing query \"What is the best kind of toad? Only say its name.\""

    assert set(result.keys()) == {
        "x", "prompt", "responses"
    }


def test_gpt_3_5_response_token_scores():
    gpt = Test(Params(model_name="yes_no"))
    results_stream = gpt.run(iter([
        {"x": "bear", "prompt": "Do you like bears?"},
        {"x": "toad", "prompt": "Do you like toads?"}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["prompt"] == "Do you like bears?"
    assert result["responses"] in ("Yes", "No")
    assert result["top_tokens_logprobs"][0] <= 0
    assert result["top_tokens_logprobs"][1] <= 0

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens_logprobs"
    }

    result = results[1]
    assert result["x"] == "toad"
    assert result["prompt"] == "Do you like toads?"
    assert result["responses"] in ("Yes", "No")
    assert result["top_tokens_logprobs"][0] <= 0
    assert result["top_tokens_logprobs"][1] <= 0

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens_logprobs"
    }
