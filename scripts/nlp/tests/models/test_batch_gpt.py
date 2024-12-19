from args import BatchProcess, Params, TokenScoresFormat
from models.batch_gpt import BatchGPT


def test_gpt_3_5_batch_write():
    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.WRITE
    ))

    results_stream = gpt.run(iter([
        {"creature": "bear", "query": "What do bears eat?"},
        {"creature": "toad", "query": "What do toads eat?"}
    ]))

    results = list(results_stream)

    batch_id = results[-1]["batch_id"]
    assert results == [
        {"batch_id": batch_id}
    ]


def test_gpt_3_5_read_batch():
    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.READ,
        scores=TokenScoresFormat.FIRST_TOKEN)
    )

    batch_id = "batch_674e0a1daee08190ac1e13b30379b84b"
    results_stream = gpt.run(iter([
        {"batch_id": batch_id}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["creature"] == "bear"
    assert result["query"] == "What do bears eat?"
    assert result["input_token_count"] == 12
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "creature", "query", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }

    result = results[1]
    assert result["creature"] == "toad"
    assert result["query"] == "What do toads eat?"
    assert result["input_token_count"] == 13
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "creature", "query", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }
