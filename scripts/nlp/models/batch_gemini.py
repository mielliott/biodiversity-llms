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


@dataclass(init=True, frozen=True)
class GCPArgs():
    """Arguments for Google Cloud Platform"""
    project_id: str
    location: str
    bucket_name: str

@ModelRegistry.register("batch_gemini")
class BatchGemini(Model):
    def __init__ (self, params: Params, gcp: GCPArgs):
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
    def __init__(self, params: Params, gcp: GCPArgs) -> None:
        self.model_name = params.model_name
        self.gemini_request_args = {
            "max_tokens": params.max_tokens,
            "temperature": params.temperature,
            "top_p": params.top_p,
            "logprobs": MAX_TOP_LOGPROBS,   
        }
        
        self.timeout = params.timeout
        self.output_uri = ""

        self.project_id = gcp.project_id
        self.location = gcp.location
        self.bucket_name = gcp.bucket_name
        self.credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


    def create_req_objects(self, queries):
        """Reference: https://ai.google.dev/api/generate-content#v1beta.GenerationConfig"""
        generation_configs = {
            "temperature": 1,
            "topP": 0.7,
            "maxOutputTokens": 100,
            "responseLogprobs": True,
            "logprobs": 5,
        }

        for query in queries:
            request = {
                "request": {
                    "contents": [{
                        "parts": {
                            "text": query
                        },
                        "role": "user"
                    }],
                    "generation_config": generation_configs
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
        print(f"Uploaded input file to {gcs_input_uri}")

        gcs_output_dest = f"gs://{self.bucket_name}/outputs/batch_results_{batch_id}"
        genai_client.batches.create(
            model=self.model_name,
            src=gcs_input_uri,
            config=CreateBatchJobConfig(dest=gcs_output_dest)
        )

        yield {"batch_id": batch_id}
        

class BatchReader(BatchHandler):
    def __init__(self, params: Params, gcp: GCPArgs) -> None:
        self.token_score_format = params.scores
        
        self.project_id = gcp.project_id
        self.location = gcp.location
        self.bucket_name = gcp.bucket_name
        self.credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    
    def run (self, queries):
        for query in queries:
            batch_id = query["batch_id"]
            yield from self.read_batch(batch_id)
            
    def read_batch(self, batch_id):
        batch_resource_name = f"projects/{self.project_id}/locations/{self.location}/batchPredictionJobs/{batch_id}"
        genai_client = genai.Client(
            vertexai=True, 
            project=self.project_id, 
            location=self.location
        )
        storage_client = storage.Client(credentials=self.credentials)
        batch_bucket = storage_client.bucket(self.bucket_name)
        
        batch = genai_client.batches.get(name=batch_resource_name)
        
        match batch.state:
            case JobState.JOB_STATE_FAILED:
                raise RuntimeError(f"Batch failed: {batch.error_file_id}")
            case JobState.JOB_STATE_PENDING:
                raise RuntimeError("Batch is still in progress")
            case JobState.JOB_STATE_SUCCEEDED:
                if not batch.output_file_id:
                    raise RuntimeError("Batch is marked \"completed\" but results are missing")
                
                output_blob = batch_bucket.blob(
                    f"outputs/batch_results_{batch_id}/0")
                output_content = output_blob.download_as_string().decode('utf-8')
                
                for line in output_content.strip().split('\n'):
                    if not line:
                        continue
                    query_response_data = json.loads(line)
                    """Reference: https://ai.google.dev/api/generate-content#v1beta.GenerateContentResponse"""
                    chat_completion = query_response_data["response"]
                    for query_response in self.process_results(chat_completion):
                        print('something', query_response)
                        yield {
                            "batch_id": batch_id,
                        } | query_response
            case _:
                raise NotImplementedError(
                    f"Unexpected batch status \"{batch.status}\"")
            
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
                    (token_data["candidates"]["token"], token_data["candidates"]["logProbability"])
                    for token_data in chat_completion_choice["logprobsResult"]["topCandidates"]
                ]
                return chat_completion_choice["content"]["parts"]["text"], response_token_logprobs
            case _:
                raise NotImplementedError(self.token_score_format)
