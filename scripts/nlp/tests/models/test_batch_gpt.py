
from types import SimpleNamespace
import openai
import openai.resources
from args import BatchProcess, Params, TokenScoresFormat
from models.batch_gpt import BatchGPT
from tests.test_util import mock_static


def test_gpt_3_5_batch_write(monkeypatch):
    def mock_batches_create(*args, input_file_id, **kwargs):
        assert input_file_id == "file-test"
        return SimpleNamespace(id="batch-test")

    monkeypatch.setattr(openai.resources.files.Files, "create", mock_static(id="file-test"))
    monkeypatch.setattr(openai.resources.batches.Batches, "create", mock_batches_create)

    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.WRITE
    ))

    results_stream = gpt.run(iter([
        {"query_number": 0, "pattern_number": 0, "creature": "bear", "prompt": "What do bears eat?"},
        {"query_number": 1, "pattern_number": 0, "creature": "toad", "prompt": "What do toads eat?"}
    ]))

    results = list(results_stream)

    assert results == [
        {"batch_id": "batch-test"}
    ]


def test_gpt_3_5_read_batch(monkeypatch):
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
    assert result["prompt"] == "What do bears eat?"
    assert result["input_token_count"] == 12
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "creature", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }

    result = results[1]
    assert result["creature"] == "toad"
    assert result["prompt"] == "What do toads eat?"
    assert result["input_token_count"] == 13
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert set(result.keys()) == {
        "creature", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    }
