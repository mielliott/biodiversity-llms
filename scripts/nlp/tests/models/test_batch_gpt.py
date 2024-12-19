
import json
from types import SimpleNamespace
import openai
import openai.resources
from args import BatchProcess, Params, TokenScoresFormat
from models.batch_gpt import BatchGPT
from tests.test_util import mock_static


def test_gpt_3_5_batch_write(monkeypatch):
    def mock_batches_create(*args, input_file_id, **kwargs):
        assert input_file_id == "file-0"
        return SimpleNamespace(id="batch-0")

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
        {"batch_id": "batch-0"}
    ]


def test_gpt_3_5_read_batch(monkeypatch):
    def mock_files_content(_, file_id):
        assert file_id == "file-1"
        mock_completion = json.dumps({
            "custom_id": "{\"query_number\": 0, \"pattern_number\": 0}",
            "response": {
                "body": {
                    "choices": [
                        {
                            "message": {
                                "content": "Fish"
                            },
                            "logprobs": {
                                "content": [
                                    {
                                        "top_logprobs": [
                                            {"token": "Fish", "logprob": -1.0},
                                            {"token": "Tree", "logprob": -2.0},
                                            {"token": "Dirt", "logprob": -3.0},
                                            {"token": "Meat", "logprob": -4.0},
                                            {"token": "Bone", "logprob": -5.0},
                                        ]
                                    }
                                ]
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0
                    }
                }
            }
        })
        return SimpleNamespace(iter_lines=lambda: (mock_completion, mock_completion))

    def mock_batches_retrieve(_, batch_id, *args, **kwargs):
        assert batch_id == "batch-0"
        return SimpleNamespace(
            status="completed",
            output_file_id="file-1"
        )

    monkeypatch.setattr(openai.resources.files.Files, "content", mock_files_content)
    monkeypatch.setattr(openai.resources.batches.Batches, "retrieve", mock_batches_retrieve)

    gpt = BatchGPT(Params(
        model_name="gpt-3.5-turbo-0125",
        batch=BatchProcess.READ,
        scores=TokenScoresFormat.FIRST_TOKEN)
    )

    results_stream = gpt.run(iter([
        {"batch_id": "batch-0"}
    ]))

    results = list(results_stream)

    assert len(results) == 2
    assert results[0] == {'query_number': 0, 'pattern_number': 0, 'responses': 'Fish', 'top_tokens': ['Fish', 'Tree', 'Dirt', 'Meat', 'Bone'], 'top_tokens_logprobs': [-1.0, -2.0, -3.0, -4.0, -5.0], 'input_token_count': 0, 'output_token_count': 0}
    assert results[1] == {'query_number': 0, 'pattern_number': 0, 'responses': 'Fish', 'top_tokens': ['Fish', 'Tree', 'Dirt', 'Meat', 'Bone'], 'top_tokens_logprobs': [-1.0, -2.0, -3.0, -4.0, -5.0], 'input_token_count': 0, 'output_token_count': 0}
