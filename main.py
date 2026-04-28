import os
import tempfile
from datetime import timedelta
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from google.cloud import storage
from pydantic import BaseModel

from create_ringtone import create_ringtone
from generate_script import generate_script
from sample_speaker import sample_speaker
from utils import get_ringtone_output_path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GCS_BUCKET     = os.environ["GCS_BUCKET"]          # e.g. "my-ringtone-bucket"
UPLOAD_PREFIX  = "uploads"                          # contacts/{user_id}/...
OUTPUT_PREFIX  = "ringtones"                        # ringtones/{user_id}/...
URL_TTL        = timedelta(minutes=15)

gcs = storage.Client()
bucket = gcs.bucket(GCS_BUCKET)

app = FastAPI()


# ---------------------------------------------------------------------------
# GCS helpers
# ---------------------------------------------------------------------------

def signed_upload_url(blob_path: str) -> str:
    return bucket.blob(blob_path).generate_signed_url(
        version="v4",
        expiration=URL_TTL,
        method="PUT",
        content_type="application/octet-stream",
    )

def signed_download_url(blob_path: str) -> str:
    return bucket.blob(blob_path).generate_signed_url(
        version="v4",
        expiration=URL_TTL,
        method="GET",
    )

def download_blob_to_tempfile(blob_path: str, suffix: str = "") -> str:
    """Download a GCS blob to a local temp file; returns the temp file path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    bucket.blob(blob_path).download_to_filename(tmp.name)
    return tmp.name

def upload_file_to_gcs(local_path: str, blob_path: str) -> None:
    bucket.blob(blob_path).upload_from_filename(local_path)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class UploadURLRequest(BaseModel):
    user_id: str
    filename: str                    # e.g. "caller_voice.wav"

class RingtoneRequest(BaseModel):
    user_id: str
    caller_voice_blob: str = None    # GCS path set after upload, e.g. "uploads/u1/caller_voice.wav"
    probability: float = 0.5

class DownloadURLRequest(BaseModel):
    user_id: str
    filename: str                    # e.g. "ringtone.wav"


# ---------------------------------------------------------------------------
# Step 1 — Phone requests a signed upload URL
# ---------------------------------------------------------------------------

@app.post("/upload-url")
async def request_upload_url(req: UploadURLRequest):
    blob_path = f"{UPLOAD_PREFIX}/{req.user_id}/{req.filename}"
    return {
        "upload_url": signed_upload_url(blob_path),
        "blob_path":  blob_path,
    }


# ---------------------------------------------------------------------------
# Step 2 — Generate ringtone (reads caller voice from GCS, writes output back)
# ---------------------------------------------------------------------------

@app.post("/generate")
async def generate_ringtone_endpoint(request: RingtoneRequest):
    if not 0.0 <= request.probability <= 1.0:
        raise HTTPException(status_code=400, detail="Probability must be between 0.0 and 1.0")

    try:
        # Fetch caller voice from GCS into a temp file (if provided)
        if request.caller_voice_blob:
            caller_speech = download_blob_to_tempfile(request.caller_voice_blob, suffix=".wav")
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

        # Upload finished ringtone to GCS
        output_blob = f"{OUTPUT_PREFIX}/{request.user_id}/{speaker}_ringtone.wav"
        upload_file_to_gcs(local_output, output_blob)

        return {
            "status":        "success",
            "speaker":       speaker,
            "famous_person": famous_person,
            "output_blob":   output_blob,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 3 — Phone requests a signed download URL for the finished ringtone
# ---------------------------------------------------------------------------

@app.post("/download-url")
async def request_download_url(req: DownloadURLRequest):
    blob_path = f"{OUTPUT_PREFIX}/{req.user_id}/{req.filename}"
    if not bucket.blob(blob_path).exists():
        raise HTTPException(status_code=404, detail="Ringtone not found")
    return {"download_url": signed_download_url(blob_path)}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)