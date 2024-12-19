from args import Params, TokenScoresFormat
from models.gpt import GPT


def test_gpt_3_5_first_token_scores():
    gpt = GPT(Params(model_name="gpt-3.5-turbo-0125", scores=TokenScoresFormat.FIRST_TOKEN))
    results_stream = gpt.run(iter([
        {"x": "bear", "prompt": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "prompt": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["prompt"] == "What is the best kind of bear? Only say its name."
    assert result["input_token_count"] == 20
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }

    result = results[1]
    assert result["x"] == "toad"
    assert result["prompt"] == "What is the best kind of toad? Only say its name."
    assert result["input_token_count"] == 21
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }


def test_gpt_3_5_response_token_scores():
    gpt = GPT(Params(model_name="gpt-3.5-turbo-0125", scores=TokenScoresFormat.RESPONSE_TOKENS))
    results_stream = gpt.run(iter([
        {"x": "bear", "prompt": "Repeat after me: bear"},
        {"x": "bear bear bear", "prompt": "Repeat after me: bear bear bear"}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["prompt"] == "Repeat after me: bear"
    assert result["input_token_count"] == 12
    assert len(result["top_tokens"]) == 1
    assert len(result["top_tokens_logprobs"]) == 1

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }

    result = results[1]
    assert result["x"] == "bear bear bear"
    assert result["prompt"] == "Repeat after me: bear bear bear"
    assert result["input_token_count"] == 14
    assert len(result["top_tokens"]) == 3
    assert len(result["top_tokens_logprobs"]) == 3

    assert set(result.keys()) == {
        "x", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }
