"""
GCP_tester.py — End-to-end test for the ringtone Cloud Run service.

Flow:
    0. GET /health                  →  verify service is reachable
    1. Request a signed upload URL  →  PUT local .mp3 to GCS
    2. POST /generate               →  trigger ringtone synthesis
    3. Request a signed download URL →  GET finished .wav to disk
"""

import subprocess
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config — edit these two lines
# ---------------------------------------------------------------------------

SERVICE_URL = "https://create-ringtone-996521322298.europe-west1.run.app"   # no trailing slash
USER_ID     = "tester"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

UPLOAD_FILE   = Path("voice_clips_tester/Friends/Mille/mille_high_pitch.mp3")
OUTPUT_FILE   = Path("voice_clips_tester/output_GCP/mille_high_pitch.wav")
UPLOAD_NAME   = "mille_high_pitch.mp3"
OUTPUT_NAME   = "mille_tester.wav"           # must match what /generate writes

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_identity_token() -> str:
    result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()

def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def step0_health(token: str) -> None:
    print("\n[0/3] Checking service health ...")
    resp = requests.get(
        f"{SERVICE_URL}/health",
        headers=headers(token),
    )
    resp.raise_for_status()
    print(f"      ✓ Health: {resp.json()}")

def step1_upload(token: str, upload_file: Path) -> str:
    print(f"\n[1/3] Requesting signed upload URL for '{upload_file.name}' ...")
    resp = requests.post(
        f"{SERVICE_URL}/upload-url",
        json={"user_id": USER_ID, "filename": UPLOAD_NAME},
        headers=headers(token),
    )
    if resp.status_code != 200:
        print(f"      ✗ Error {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    upload_url = data["upload_url"]
    blob_path  = data["blob_path"]

    print(f"      Uploading {upload_file} → GCS ...")
    with open(upload_file, "rb") as f:
        put = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": "application/octet-stream"},
        )
    put.raise_for_status()
    print(f"      ✓ Uploaded  (blob: {blob_path})")
    return blob_path


def step2_generate(token: str, blob_path: str) -> str:
    print("\n[2/3] Triggering ringtone generation ...")
    resp = requests.post(
        f"{SERVICE_URL}/generate",
        json={
            "user_id":           USER_ID,
            "caller_voice_blob": blob_path,
            "probability":       0.5,
        },
        headers=headers(token),
        timeout=120,   # generation can take a while
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"      ✓ Done  (speaker: {data['speaker']}, famous_person: {data['famous_person']})")
    print(f"        output blob: {data['output_blob']}")
    return data["output_blob"]


def step3_download(token: str, output_file: Path) -> None:
    print(f"\n[3/3] Requesting signed download URL for '{OUTPUT_NAME}' ...")
    resp = requests.post(
        f"{SERVICE_URL}/download-url",
        json={"user_id": USER_ID, "filename": OUTPUT_NAME},
        headers=headers(token),
    )
    resp.raise_for_status()
    download_url = resp.json()["download_url"]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"      Downloading → {output_file} ...")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"      ✓ Saved  ({output_file.stat().st_size / 1024:.1f} KB)")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not UPLOAD_FILE.exists():
        sys.exit(f"Upload file not found: {UPLOAD_FILE}")

    token = get_identity_token()

    step0_health(token)
    blob_path = step1_upload(token, UPLOAD_FILE)
    step2_generate(token, blob_path)
    step3_download(token, OUTPUT_FILE)

    print(f"\n✅  All done — ringtone saved to {OUTPUT_FILE}")