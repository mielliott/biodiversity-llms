import json
import pytest
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from args import BatchProcess, Params, TokenScoresFormat
from models.batch_gemini import BatchGemini


@pytest.fixture(autouse=True)
def mock_gcp_env_vars(monkeypatch):
    def mock_getenv(key, default=None):
        env_values = {
            "GCP_PROJECT_ID": "test-project",
            "GCP_LOCATION": "us-central1",
            "GCP_STORAGE_BUCKET_NAME": "test-bucket",
            "GOOGLE_APPLICATION_CREDENTIALS": "fake_credentials.json"
        }
        return env_values.get(key, default)

    monkeypatch.setattr("os.getenv", mock_getenv)
    yield


@pytest.fixture
def patch_google_apis(monkeypatch):
    # Create storage mocks
    mock_storage_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    # Create genai mocks
    mock_genai_client = MagicMock()
    mock_batches = MagicMock()
    mock_genai_client.batches = mock_batches
    mock_batch = MagicMock()
    mock_batches.create.return_value = mock_batch
    mock_batches.get.return_value = SimpleNamespace(
        state="JOB_STATE_SUCCEEDED",
        output_file_id="output-file-1"
    )

    # Set up patches
    mock_credentials = MagicMock()
    monkeypatch.setattr("google.cloud.storage.Client",
                        lambda **kwargs: mock_storage_client)
    monkeypatch.setattr("google.genai.Client", lambda **
                        kwargs: mock_genai_client)
    monkeypatch.setattr("google.oauth2.service_account.Credentials.from_service_account_file", 
                        lambda filename: mock_credentials)
    monkeypatch.setattr("uuid.uuid4", lambda: SimpleNamespace(hex="fakeuuid12345678"))
    
    return {
        "storage": {
            "client": mock_storage_client,
            "bucket": mock_bucket,
            "blob": mock_blob
        },
        "genai": {
            "client": mock_genai_client,
            "batches": mock_batches,
            "batch": mock_batch
        },
        "credentials": mock_credentials
    }


def test_gemini_batch_write(patch_google_apis):
    gemini = BatchGemini(
        Params(model_name="gemini-1.5-flash", batch=BatchProcess.WRITE),
    )

    test_data = [
        {"query_number": 0, "pattern_number": 0, "prompt": "What do bears eat?"},
        {"query_number": 1, "pattern_number": 0, "prompt": "What do toads eat?"}
    ]
    results = list(gemini.run(test_data))

    # mock assertions
    assert patch_google_apis["storage"]["client"].bucket.called
    assert patch_google_apis["storage"]["bucket"].blob.called
    assert patch_google_apis["storage"]["blob"].upload_from_string.called
    assert patch_google_apis["genai"]["batches"].create.called

    assert len(results) == 1
    assert "batch_id" in results[0]


def test_gemini_batch_read(patch_google_apis):
    mock_gemini_response = {
        "status": "",
        "processed_time": "2025-03-17T16:56:31.816+00:00",
        "request": {
            "contents": [
                {
                    "parts": {"text": "What do bears eat?"},
                    "role": "user"
                }
            ],
            "generation_config": {
                "responseLogprobs": True, 
                "logprobs": 5
            }
        },
        "response": {
            "candidates": [
                {
                    "avgLogprobs": -0.07164737701416016,
                    "content": {
                        "parts": [{"text": "Bears eat a variety of foods including berries, fish, and honey."}],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "logprobsResult": {
                        "topCandidates": [
                            {
                                "candidates": [
                                    {"token": "Bears", "logProbability": -0.01},
                                    {"token": "The", "logProbability": -1.5},
                                    {"token": "These", "logProbability": -2.0},
                                    {"token": "Most", "logProbability": -3.0},
                                    {"token": "Wild", "logProbability": -3.5}
                                ]
                            }
                        ]
                    }
                }
            ],
            "createTime": "2025-03-17T16:56:31.843123Z",
            "modelVersion": "gemini-1.5-flash-002@default",
            "responseId": "P1TYZ_O6M42ShMIPjNqGeQ",
            "usageMetadata": {
                "promptTokenCount": 5,
                "candidatesTokenCount": 15,
                "totalTokenCount": 20
            }
        },
    }

    mock_responses = [
        json.dumps(mock_gemini_response),
        # tweak the second response
        json.dumps({**mock_gemini_response, 
                   "response": {**mock_gemini_response["response"], 
                                "candidates": [{**mock_gemini_response["response"]["candidates"][0], 
                                              "content": {"parts": [{"text": "Toads eat insects, worms, and small invertebrates."}], 
                                                         "role": "model"}}]}})
    ]
    # setup the return value for download_as_string
    mock_response_bytes = MagicMock()
    mock_response_bytes.decode.return_value = "\n".join(mock_responses)
    patch_google_apis["storage"]["blob"].download_as_string.return_value = mock_response_bytes

    gemini = BatchGemini(
        Params(
            model_name="gemini-1.5-flash",
            batch=BatchProcess.READ,
            scores=TokenScoresFormat.FIRST_TOKEN,
        )
    )

    results = list(gemini.run(iter([
        {"batch_id": "batch-0"}
    ])))

    assert len(results) == 2
    assert results[0]["batch_id"] == "batch-0"
    assert "Bears eat a variety of foods including berries, fish, and honey." in results[0]["responses"]
    assert results[0]["top_tokens"] == ["Bears", "The", "These", "Most", "Wild"]
    assert results[0]["top_tokens_logprobs"] == [-0.01, -1.5, -2.0, -3.0, -3.5]
    assert results[1]["batch_id"] == "batch-0"
    assert "Toads eat insects, worms, and small invertebrates." in results[1]["responses"]
