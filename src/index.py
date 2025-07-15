import httpx
import os

from fastapi import FastAPI, HTTPException, Request, Depends, Security, UploadFile, File, Form
from fastapi.responses import StreamingResponse, RedirectResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

API_KEY = os.getenv('API_KEY')
API_KEY_NAME = "x-api-key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Start the API
app = FastAPI()

# Create the security scheme for Bearer tokens
bearer_scheme = HTTPBearer(auto_error=False)

# configure CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


def get_api_key(header_api_key: str = Security(api_key_header)):
    """
    Validate the API key provided in the request header.

    This function checks if the API key provided in the x-api-key header
    matches the expected API key from the environment variable.

    Args:
        header_api_key: The API key extracted from the request header

    Returns:
        str: The validated API key if authentication is successful

    Raises:
        HTTPException: 403 error if the API key is invalid or missing
    """
    if header_api_key == API_KEY:
        return header_api_key
    else:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )

def get_bearer_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    """
    Validate the Bearer token from the Authorization header.

    Args:
        credentials: The Bearer token credentials extracted from the Authorization header

    Returns:
        The validated token if authentication is successful

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header with Bearer token"
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Authorization header must use Bearer scheme"
        )

    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )

    return credentials.credentials

@app.get("/", include_in_schema=False)
def root():
    """Redirect to the API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    status = {
        "api_status": "ok",
        "whisper_status": "unknown"
    }

    whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "http://whisper:9000")

    try:
        # Create a client with a short timeout for health check
        client = httpx.AsyncClient(base_url=whisper_endpoint, timeout=5.0)
        # Check if Whisper's health endpoint is accessible
        response = await client.get("/")

        if response.status_code == 200:
            status["whisper_status"] = "ok"
        else:
            status["whisper_status"] = f"error: received status code {response.status_code}"

    except Exception as e:
        status["whisper_status"] = f"error: {str(e)}"
    finally:
        await client.aclose()

    # Return 200 if both services are okay, otherwise 503
    http_status = 200 if status["whisper_status"] == "ok" else 503

    return JSONResponse(content=status, status_code=http_status)


@app.post("/asr")
async def whisper(
     request: Request,
#      audio_file: UploadFile = File(...),
#      encode: bool = Query(default=True, description="Encode audio first through ffmpeg"),
#      task: Union[str, None] = Query(default="transcribe", enum=["transcribe", "translate"]),
#      language: Union[str, None] = Query(default=None, description="Language to use"),
#      word_timestamps: bool = Query(default=False, description="Word level timestamps"),
#      output: Union[str, None] = Query(default="txt", enum=["txt", "vtt", "srt", "tsv", "json"])
     api_key: str = Depends(get_api_key, use_cache=False)
    ):
    """
      This forwards the file upload request to whisper and therefor is is not
      possible to have the right swagger docs. See whisper API for
      documentation.

      <strong>CURL example:</strong>
      <pre>
      curl -X 'POST' 'http://whisper.local.itkdev.dk/api/whisper/asr?encode=true&task=transcribe&language=da&word_timestamps=false&output=json'
           -H 'accept: application/json'
           -H 'Content-Type: multipart/form-data'
           -F 'audio_file=@sample-0.mp3;type=audio/mpeg'</pre>
    """
    whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "http://whisper:9000")

    client = httpx.AsyncClient(base_url=whisper_endpoint, timeout=3600.0)
    url = httpx.URL(path='/asr', query=request.url.query.encode("utf-8"))
    rp_req = client.build_request('POST', url, headers=request.headers.raw, content=request.stream())
    rp_resp = await client.send(rp_req, stream=True)

    return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers
        )


@app.post("/audio/transcriptions")
async def transcribe_audio(
        request: Request,
        file: UploadFile = File(...),
        model: Optional[str] = Form(None),
        language: Optional[str] = Form(None),
        token: str = Depends(get_bearer_token, use_cache=False)
    ):
    """
    Transcribe audio using the local Whisper service.

    Parameters:
    - file: The audio file to transcribe
    - model: The model to use for transcription (this has no effect on the local Whisper service, but here for compatibility with OpenAI)
    - language: The language of the audio file
    """
    # Check authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Must be in format: 'Bearer YOUR_API_KEY'"
        )

    # Extract the API key from the Authorization header
    api_key = auth_header.split("Bearer ")[1].strip()

    # Validate the API key (you may want to use your existing API key or a different one)
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid token"
        )

    # Prepare query parameters
    query_params = {"task": "transcribe"}

    # Add language if provided
    if language:
        query_params["language"] = language

    # Set output format to JSON
    query_params["output"] = "json"

    # Set encoding to true to process through ffmpeg
    query_params["encode"] = "true"

    # Create a temporary file with the content from the uploaded file
    file_content = await file.read()

    # Prepare multipart form data for the request to Whisper
    files = {"audio_file": (file.filename, file_content, file.content_type)}

    # Send request to local Whisper service
    whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "http://whisper:9000")
    client = httpx.AsyncClient(base_url=whisper_endpoint, timeout=3600.0)
    response = await client.post("/asr", params=query_params, files=files)

    # Check if the response was successful
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Whisper service error: {response.text}"
        )

    # Parse the response from Whisper
    whisper_response = response.json()

    # Format the response to match OpenAI's transcription API response format
    formatted_response = {
        "text": whisper_response.get("text", "")
    }

    # Add any additional fields that might be present in the OpenAI response format
    # based on the Whisper response

    return JSONResponse(
        content=formatted_response,
        status_code=200
    )
