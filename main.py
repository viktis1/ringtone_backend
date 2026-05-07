import os
import tempfile
import subprocess
from datetime import datetime, timedelta
from fastapi.responses import Response
import asyncio
import uuid
 
from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
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
UPLOAD_PREFIX  = "uploads"                          # uploads/{user_id}_{datetime}
OUTPUT_PREFIX  = "ringtones"                        # ringtones/{user_id}_{datetime}
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
    if blob_path is None:
        return False # Syntax for no caller speech, can be handled by sample_speaker.
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
    blob.upload_from_string(contents, content_type=file.content_type) # blocks the event loop but small file.
    return {"status": "ok", "blob_path": f"{UPLOAD_PREFIX}/{file.filename}"}


# # ---------------------------------------------------------------------------
# # Step 2 — Generate ringtone - async because this step takes ~ 10 min
# # ---------------------------------------------------------------------------
# Define the jobs since it is not a synchronous HTTP connection - GitHub actions didn't want to wait that long.
jobs: dict[str, dict] = {}


def _run_generate(job_id: str, request: RingtoneRequest):
    """Runs synchronously."""
    try:
        jobs[job_id]["status"] = "running"

        caller_speech = get_file_from_gcs(request.caller_voice_path, suffix=".wav") # False if no caller speech

        speaker, famous_person, voice_path = sample_speaker(
            p=request.probability, caller_speech=caller_speech
        )
        script = generate_script(
            receiver="Viktor", caller="Mille",
            speaker=speaker, famous_person=famous_person,
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
            local_output = tmp_out.name
            create_ringtone(
                text=script,
                reference_wav_path=voice_path,
                output_path=local_output,
                model_path=GCS_BUCKET + "/weights/VoxCPM2"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            output_blob = f"{OUTPUT_PREFIX}/{request.user_id}/{speaker}_ringtone_{timestamp}.wav"
            push_file_to_gcs(local_output, output_blob)

        jobs[job_id] = {
            "status":       "done",
            "speaker":      speaker,
            "famous_person": famous_person,
            "output_blob":  output_blob,
        }

    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}


@app.post("/generate")
async def generate_ringtone_endpoint(request: RingtoneRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued"}
    background_tasks.add_task(_run_generate, job_id, request)
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ---------------------------------------------------------------------------
# Step 3 — Phone requests a signed download URL for the finished ringtone
# ---------------------------------------------------------------------------

@app.post("/download")
async def download_file(request: DownloadRequest):
    blob = bucket.blob(request.blob_path)
    contents = blob.download_as_bytes() # blocks the event loop. Small file though.
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
    gpu_info = "No GPU detected"
    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode == 0:
        gpu_info = result.stdout
    else:
        gpu_info = f"nvidia-smi error: {result.stderr}"
    
    return {
        "status": "ok",
        "gpu": gpu_info,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080
    )