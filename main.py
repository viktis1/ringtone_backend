import os
import tempfile
from datetime import timedelta
from fastapi.responses import Response
 
from fastapi import FastAPI, UploadFile
from google.cloud import storage
from pydantic import BaseModel

from create_ringtone import create_ringtone
from generate_script import generate_script
from sample_speaker import sample_speaker
from utils import get_ringtone_output_path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GCS_BUCKET     = os.environ["GCS_BUCKET"]          # e.g. "contact-info-bucket"
UPLOAD_PREFIX  = "uploads"                          # contacts/{user_id}/...
OUTPUT_PREFIX  = "ringtones"                        # ringtones/{user_id}/...
URL_TTL        = timedelta(minutes=15)
SERVICE_ACCOUNT_EMAIL = "ghcr-puller@ringtonechanger-494218.iam.gserviceaccount.com"

gcs = storage.Client()
bucket = gcs.bucket(GCS_BUCKET)

app = FastAPI()


# ---------------------------------------------------------------------------
# GCS helpers
# ---------------------------------------------------------------------------

def get_file_from_gcs(blob_path: str, suffix: str = "") -> str:
    """Download a GCS blob to a local temp file, return the local path."""
    blob = bucket.blob(blob_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        blob.download_to_filename(tmp.name)
        return tmp.name

def push_file_to_gcs(local_path: str, blob_path: str) -> None:
    """Upload a local file to GCS."""
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RingtoneRequest(BaseModel):
    user_id: str
    caller_voice_path: str = None    # GCS path set after upload
    probability: float = 0.5

class DownloadRequest(BaseModel):                 
    blob_path: str                                #   e.g. output_blob from /generate


# ---------------------------------------------------------------------------
# Step 1 — Upload from phone to GSC
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_file(file: UploadFile):
    contents = await file.read()
    blob = bucket.blob(f"{UPLOAD_PREFIX}/{file.filename}")   # ← use global bucket
    blob.upload_from_string(contents, content_type=file.content_type)
    return {"status": "ok", "blob_path": f"{UPLOAD_PREFIX}/{file.filename}"}


# # ---------------------------------------------------------------------------
# # Step 2 — Generate ringtone (reads caller voice from GCS, writes output back)
# # ---------------------------------------------------------------------------

@app.post("/generate")
async def generate_ringtone_endpoint(request: RingtoneRequest):

    # Fetch caller voice from GCS into a temp file (if provided)
    if request.caller_voice_path:
        caller_speech = get_file_from_gcs(request.caller_voice_path, suffix=".wav")
    else:
        caller_speech = False

    # Sample speaker, generate script, synthesise
    speaker, famous_person, voice_path = sample_speaker(
        p=request.probability, caller_speech=caller_speech
    )
    script = generate_script(
        receiver="Viktor", caller="Mille",
        speaker=speaker, famous_person=famous_person,
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
        local_output = tmp_out.name
        create_ringtone(text=script, reference_wav_path=voice_path, output_path=local_output)
        output_blob = f"{OUTPUT_PREFIX}/{request.user_id}/{speaker}_ringtone.wav"
        push_file_to_gcs(local_output, output_blob)
        

    return {
        "status":        "success",
        "speaker":       speaker,
        "famous_person": famous_person,
        "output_blob":   output_blob,
    }


# ---------------------------------------------------------------------------
# Step 3 — Phone requests a signed download URL for the finished ringtone
# ---------------------------------------------------------------------------

@app.post("/download")
async def download_file(request: DownloadRequest):
    blob = bucket.blob(request.blob_path)
    contents = blob.download_as_bytes()
    return Response(
        content=contents,
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename={request.blob_path.split('/')[-1]}"}
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)