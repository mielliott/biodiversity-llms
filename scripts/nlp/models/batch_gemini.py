from dataclasses import dataclass
import os
import uuid
import json
from google import genai
from google.cloud import storage
from google.genai.types import CreateBatchJobConfig, JobState, HttpOptions
from utils.file_like_object import FileLikeObject

from google.oauth2 import service_account

from args import Params, BatchProcess, TokenScoresFormat
from .model import Model
from .registry import ModelRegistry

MAX_TOP_LOGPROBS = 5 # limits for Gemini


"""
Examples:
Create Batch: 
    echo -e "species\tlocation\nAcer saccharum\tArkansas" | python main.py -mc "batch_gemini" -m "gemini-1.5-flash-002" --batch write "Does {species} naturally occur in {location}? Yes or no"
    
    # outputs: batch_id


Read Batch: 
    echo -e "species\tlocation\tbatch_id\nAcer saccharum\tArkansas\tprojects/{gcpProjectId}/locations/{gcpLocation}/batchPredictionJobs/{batchJobName}" | python main.py -mc "batch_gemini" -m "gemini-1.5-flash-002" --batch read --scores first_token
"""

@dataclass(init=True, frozen=True)
class GcpArgs():
    """Arguments for Google Cloud Platform"""
    project_id: str
    location: str
    bucket_name: str

@ModelRegistry.register("batch_gemini")
class BatchGemini(Model):
    def __init__(self, params: Params):
        gcp: GcpArgs = {
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "location": os.getenv("GCP_LOCATION"),
            "bucket_name": os.getenv("GCP_STORAGE_BUCKET_NAME")
        }

        match params.batch:
            case BatchProcess.WRITE:
                self.handler = BatchWriter(params, gcp)
            case BatchProcess.READ:
                self.handler = BatchReader(params, gcp)
            case BatchProcess.NONE:
                raise RuntimeError("Please specify --batch write or --batch read")
            
    def load_model(self):
        # Gemini Models are served through Google API
        pass
    
    def get_model_info(self):
        return {"name": "batch_gemini"}
    
    def run(self, queries):
        yield from self.handler.run(queries)
            
            
class BatchHandler():
    def run(self, queries):
        yield from []


class BatchWriter(BatchHandler):
    def __init__(self, params: Params, gcp: GcpArgs) -> None:
        self.model_name = params.model_name

        """Reference: https://ai.google.dev/api/generate-content#v1beta.GenerationConfig"""
        self.generation_configs = {}
        if params.max_tokens is not None:
            self.generation_configs["maxOutputTokens"] = params.max_tokens
        if params.temperature is not None:
            self.generation_configs["temperature"] = params.temperature
        if params.top_p is not None:
            self.generation_configs["topP"] = params.top_p

        self.generation_configs["responseLogprobs"] = True
        self.generation_configs["logprobs"] = MAX_TOP_LOGPROBS
        
        self.timeout = params.timeout
        self.output_uri = ""

        self.project_id = gcp["project_id"]
        self.location = gcp["location"]
        self.bucket_name = gcp["bucket_name"]
        self.credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


    def create_req_objects(self, queries):
        for query in queries:
            request = {
                "request": {
                    "contents": [{
                        "parts": {
                            "text": query["prompt"]
                        },
                        "role": "user"
                    }],
                    "generation_config": self.generation_configs
                }
            }
            yield (json.dumps(request) + "\n").encode()
        

    def run(self, queries):
        """Create, upload and run a batch job for the given queries"""
        requests = self.create_req_objects(queries)
        requests_byte_stream = FileLikeObject(requests)
        
        batch_id = uuid.uuid4().hex[:8]
        genai_client = genai.Client(
            vertexai=True, 
            project=self.project_id, 
            location=self.location
        )
        storage_client = storage.Client(credentials=self.credentials)
        batch_bucket = storage_client.bucket(self.bucket_name)

        gcs_input_path = f"inputs/batch_inputs_{batch_id}.jsonl"
        blob = batch_bucket.blob(gcs_input_path)
        blob.upload_from_string(requests_byte_stream.read())
        
        gcs_input_uri = f"gs://{self.bucket_name}/{gcs_input_path}"
        gcs_output_dest = f"gs://{self.bucket_name}/outputs/batch_results_{batch_id}"

        job = genai_client.batches.create(
            model=self.model_name,
            src=gcs_input_uri,
            config=CreateBatchJobConfig(dest=gcs_output_dest)
        )

        yield {"batch_id": job.name}
        

class BatchReader(BatchHandler):
    def __init__(self, params: Params, gcp: GcpArgs) -> None:
        self.token_score_format = params.scores
        
        self.project_id = gcp["project_id"]
        self.location = gcp["location"]
        self.bucket_name = gcp["bucket_name"]
        self.credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    
    def run (self, queries):
        for query in queries:
            batch_id = query["batch_id"]
            yield from self.read_batch(batch_id)
            
    def read_batch(self, batch_id):
        genai_client = genai.Client(
            vertexai=True, 
            project=self.project_id, 
            location=self.location
        )
        
        batch = genai_client.batches.get(name=batch_id)
        
        match batch.state:
            case JobState.JOB_STATE_FAILED:
                raise RuntimeError(f"Batch failed: {batch.error_file_id}")
            case JobState.JOB_STATE_PENDING:
                raise RuntimeError("Batch is still in progress")
            case JobState.JOB_STATE_RUNNING:
                raise RuntimeError("Batch is still running")
            case JobState.JOB_STATE_SUCCEEDED:
                if not batch.dest.gcs_uri:
                    raise RuntimeError("Batch is marked \"completed\" but results are missing")
                output_folder_uri = batch.dest.gcs_uri
                # Parse the GCS URI to get prefix
                # Format: gs://bucket-name/path/to/folder
                uri_parts = output_folder_uri.replace(
                    "gs://", "").split("/", 1)
                bucket_name = uri_parts[0]
                prefix = uri_parts[1] if len(uri_parts) > 1 else ""

                storage_client = storage.Client(credentials=self.credentials)
                batch_bucket = storage_client.bucket(bucket_name)
                blobs = list(batch_bucket.list_blobs(prefix=prefix))
                prediction_files = [
                    blob for blob in blobs if blob.name.endswith('predictions.jsonl')]

                if prediction_files:
                    # Use the first prediction file found
                    prediction_blob = prediction_files[0]
                    output_content = prediction_blob.download_as_string().decode('utf-8')

                    for line in output_content.strip().split('\n'):
                        if not line:
                            continue
                        query_response_data = json.loads(line)
                        """Reference: https://ai.google.dev/api/generate-content#v1beta.GenerateContentResponse"""
                        chat_completion = query_response_data["response"]
                        for query_response in self.process_results(chat_completion):
                            yield {
                                "batch_id": batch_id,
                            } | query_response
                else:
                    RuntimeError("No prediction results found")

            case _:
                raise NotImplementedError(
                    f"Unexpected batch status \"{batch.state}\"")
            
    def process_results(self, chat_completion):
        for choice in chat_completion["candidates"]:
            response_text, top_token_logprobs = self.process_chat_completion(choice)
            yield {
                "responses": response_text,
                "top_tokens": [x[0] for x in top_token_logprobs],
                "top_tokens_logprobs": [x[1] for x in top_token_logprobs],
                "input_token_count": chat_completion["usageMetadata"]["promptTokenCount"],
                "output_token_count": chat_completion["usageMetadata"]["candidatesTokenCount"]
            }

    def process_chat_completion(self, chat_completion_choice):
        match self.token_score_format:
            case TokenScoresFormat.FIRST_TOKEN:
                first_token_logprobs = [
                    (candidate["token"], candidate["logProbability"])
                    for candidate in chat_completion_choice[
                    "logprobsResult"]["topCandidates"][0]["candidates"]
                ]
                return chat_completion_choice["content"]["parts"][0]["text"], first_token_logprobs
            case TokenScoresFormat.RESPONSE_TOKENS:
                response_token_logprobs = [
                    (candidate["token"], candidate["logProbability"]) for token_data in chat_completion_choice["logprobsResult"]["topCandidates"] for candidate in token_data["candidates"]
                ]
                return chat_completion_choice["content"]["parts"][0]["text"], response_token_logprobs
            case _:
                raise NotImplementedError(self.token_score_format)
