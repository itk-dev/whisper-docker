import httpx
import os

from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

API_KEY = os.getenv('API_KEY')
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Start the API
app = FastAPI()

# configure CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )

@app.get("/health")
def health():
    """Test method to verify if the api is accessible."""
    return 200

@app.post("/asr")
async def whisper(
     request: Request,
#      audio_file: UploadFile = File(...),
#      encode: bool = Query(default=True, description="Encode audio first through ffmpeg"),
#      task: Union[str, None] = Query(default="transcribe", enum=["transcribe", "translate"]),
#      language: Union[str, None] = Query(default=None, description="Language to use"),
#      word_timestamps: bool = Query(default=False, description="Word level timestamps"),
#      output: Union[str, None] = Query(default="txt", enum=["txt", "vtt", "srt", "tsv", "json"])
     api_key: str = Depends(get_api_key)
    ):
    """
      This forwards the file upload request to whisper and therefor is is not
      possible to have the right swagger docs. See whisper API for
      documentation.

      <strong>CURL example:</strong>
      <pre>
      curl -X 'POST' 'http://0.0.0.0:32811/whisper/asr?encode=true&task=transcribe&language=da&word_timestamps=false&output=json'
           -H 'accept: application/json'
           -H 'Content-Type: multipart/form-data'
           -F 'audio_file=@sample-0.mp3;type=audio/mpeg'</pre>
    """
    client = httpx.AsyncClient(base_url="http://whisper:9000/", timeout=3600.0)
    url = httpx.URL(path='/asr', query=request.url.query.encode("utf-8"))
    rp_req = client.build_request('POST', url, headers=request.headers.raw, content=request.stream())
    rp_resp = await client.send(rp_req, stream=True)

    return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers
        )
