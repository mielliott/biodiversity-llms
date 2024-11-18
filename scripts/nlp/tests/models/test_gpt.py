from args import BatchProcess, Params, TokenScoresFormat
from models.gpt import GPT
from models.batch_gpt import BatchGPT


def test_gpt_3_5_first_token_scores():
    gpt = GPT(Params(model_name="gpt-3.5-turbo-0125", scores=TokenScoresFormat.FIRST_TOKEN))
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


def test_gpt_3_5_response_token_scores():
    gpt = GPT(Params(model_name="gpt-3.5-turbo-0125", scores=TokenScoresFormat.RESPONSE_TOKENS))
    results_stream = gpt.run(iter([
        {"x": "bear", "query": "Repeat after me: bear"},
        {"x": "bear bear bear", "query": "Repeat after me: bear bear bear"}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["query"] == "Repeat after me: bear"
    assert result["question number"] == 0
    assert result["input token count"] == 12
    assert len(result["top tokens"]) == 1
    assert len(result["top tokens logprobs"]) == 1

    assert set(result.keys()) == {
        "x", "query", "responses", "question number", "top tokens", "top tokens logprobs", "input token count", "output token count"
    }

    result = results[1]
    assert result["x"] == "bear bear bear"
    assert result["query"] == "Repeat after me: bear bear bear"
    assert result["question number"] == 1
    assert result["input token count"] == 14
    assert len(result["top tokens"]) == 3
    assert len(result["top tokens logprobs"]) == 3

    assert set(result.keys()) == {
        "x", "query", "responses", "question number", "top tokens", "top tokens logprobs", "input token count", "output token count"
    }


def test_gpt_3_5_batch_write():
    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.WRITE
    ))

    results_stream = gpt.run(iter([
        {"x": "bear", "query": "What do bears eat?"},
        {"x": "toad", "query": "What do toads eat?"}
    ]))

    results = list(results_stream)
    batch_id = results[0]["batch id"]
    assert results == [
        {"x": "bear", "query": "What do bears eat?", "batch id": batch_id, "request id": "request-0"},
        {"x": "toad", "query": "What do toads eat?", "batch id": batch_id, "request id": "request-1"}
    ]


def test_gpt_3_5_read_batch():
    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.READ
    ))
    results = gpt.run(iter([
        {"x": "bear", "query": "What do bears eat?"},
        {"x": "toad", "query": "What do toads eat?"}
    ]))
    results = list(results)

    assert results[0]["x"] == "toad"
