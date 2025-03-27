import json
from types import SimpleNamespace
import anthropic
from args import BatchProcess, Params, TokenScoresFormat
from models.batch_claud import BatchClaud
from unittest.mock import MagicMock


def test_claud_batch_write(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = SimpleNamespace(id="batch-0")
    monkeypatch.setattr(anthropic, "Anthropic", lambda: mock_client)
    claud = BatchClaud(Params(
        model_name="claude-3-5-sonnet-20240620",
        batch=BatchProcess.WRITE
    ))

    results_stream = claud.run(iter([
        {"query_number": 0, "pattern_number": 0, "creature": "bear", "prompt": "What do bears eat?"},
        {"query_number": 1, "pattern_number": 0, "creature": "toad", "prompt": "What do toads eat?"}
    ]))
    results = list(results_stream)

    assert results == [
        {"batch_id": "batch-0"}
    ]
    assert mock_client.messages.create.called


def test_claud_read_batch(monkeypatch):
    mock_client = MagicMock()
    mock_batch = SimpleNamespace(processing_status="ended")
    mock_client.batches.retrieve.return_value = mock_batch

    mock_response1 = {
        "custom_id": "{\"query_number\": 0, \"pattern_number\": 0}",
        "message": {
            "content": {
                "text": "Fish"
            },
            "usage": {
                "input_tokens": 10,
                "output_tokens": 1
            }
        }
    }
    mock_response2 = {
        "custom_id": "{\"query_number\": 1, \"pattern_number\": 0}",
        "message": {
            "content": {
                "text": "Worm"
            },
            "usage": {
                "input_tokens": 10,
                "output_tokens": 1
            }
        }
    }
    mock_results = [json.dumps(mock_response1), json.dumps(mock_response2)]
    mock_client.messages.batches.results.return_value = mock_results

    monkeypatch.setattr(anthropic, "Anthropic", lambda: mock_client)
    claud = BatchClaud(Params(
        model_name="claude-3-5-sonnet-20240620",
        batch=BatchProcess.READ,
        scores=TokenScoresFormat.FIRST_TOKEN)
    )
    results_stream = claud.run(iter([
        {"batch_id": "batch-0"}
    ]))
    results = list(results_stream)

    assert len(results) == 2
    assert results[0]["batch_id"] == "batch-0"
    assert results[0]["query_number"] == 0
    assert results[0]["pattern_number"] == 0
    assert results[0]["responses"] == "Fish"
    assert results[0]["top_tokens"] == []
    assert results[0]["top_tokens_log_probs"] == []
    assert results[0]["input_token_count"] == 10
    assert results[0]["output_token_count"] == 1

    assert results[1]["batch_id"] == "batch-0"
    assert results[1]["query_number"] == 1
    assert results[1]["pattern_number"] == 0
    assert results[1]["responses"] == "Worm"
    assert results[1]["top_tokens"] == []
    assert results[1]["top_tokens_log_probs"] == []
    assert results[1]["input_token_count"] == 10
    assert results[1]["output_token_count"] == 1
