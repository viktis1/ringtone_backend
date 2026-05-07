"""
End-to-end integration test for the Ringtone Cloud Run service.
The application should work with both .mp3 and .wav input files.

This test verifies the complete workflow:
    0. GET /health              →  verify service is reachable and GPU available
    1. POST /upload             →  upload caller voice from local file
    2. POST /generate           →  trigger ringtone synthesis
    3. POST /download           →  fetch finished .wav to disk

Authentication:
    Uses Application Default Credentials (ADC):
    - Locally: run `gcloud auth application-default login` first
    - CI/CD: Configured via Workload Identity Federation in GitHub Actions

Configuration:
    SERVICE_URL   - Cloud Run service endpoint (default: env var SERVICE_URL)
    USER_ID       - Test user ID (default: env var USER_ID or "tester")
    TEST_FILES    - List of audio files to test (.mp3 and .wav)
    OUTPUT_DIR    - Where to save results (default: tests/output/)

Usage:
    # Local: First authenticate with gcloud
    gcloud auth application-default login
    python tests/test_e2e_gcp_deployment.py

    # With pytest
    pytest tests/test_e2e_gcp_deployment.py -v

    # Custom service URL
    SERVICE_URL=https://my-service.run.app python tests/test_e2e_gcp_deployment.py
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SERVICE_URL = os.getenv("SERVICE_URL", "https://create-ringtone-staging-996521322298.europe-west1.run.app")
USER_ID = os.getenv("USER_ID", "tester")

# Test files: both .mp3 and .wav formats
TEST_FILES = [
    Path("tests/fixtures/mille.mp3"),
    Path("tests/fixtures/viktor.wav"),
]
OUTPUT_DIR = Path("tests/output")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_identity_token() -> str:
    """Get an ID token for Cloud Run. The authentication should work both
      locally via gcloud auth print-identity-token and on GitHub actions 
      via Workload Identity Federation.

    Returns:
        str: Bearer token for Cloud Run authentication
    """

    # Works in CI/CD when ADC is backed by a service account
    try:
        return id_token.fetch_id_token(Request(), SERVICE_URL)
    except Exception:
        pass

    # Local fallback for local testing
    if shutil.which("gcloud"):
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    raise RuntimeError(
        "No ID token available. Use Workload Identity in CI, "
        "or run 'gcloud auth print-identity-token' locally."
    )


def headers(token: str) -> dict:
    """Return authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test Steps
# ---------------------------------------------------------------------------

def step0_health(token: str) -> None:
    """Test: Service health endpoint responds and GPU is available."""
    print("\n[0/3] Checking service health ...")
    resp = requests.get(
        f"{SERVICE_URL}/health",
        headers=headers(token),
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"      ✓ Health: status={data.get('status')}")
    if "gpu" in data:
        gpu_status = "✓ GPU detected" if "No GPU" not in data["gpu"] else "⚠ No GPU"
        print(f"      {gpu_status}")


def step1_upload(token: str, upload_file: Path) -> str:
    """Test: Upload caller voice to GCS."""
    print(f"\n[1/3] Uploading '{upload_file.name}' ...")
    
    with open(upload_file, "rb") as f:
        files = {"file": (upload_file.name, f, "application/octet-stream")}
        resp = requests.post(
            f"{SERVICE_URL}/upload",
            files=files,
            headers=headers(token),
        )
    
    resp.raise_for_status()
    data = resp.json()
    blob_path = data["blob_path"]
    print(f"      ✓ Uploaded (blob: {blob_path})")
    return blob_path


def step2_generate(token: str, blob_path: str) -> str:
    """Test: Trigger ringtone generation with TTS synthesis."""
    print("\n[2/3] Triggering ringtone generation ...")

    resp = requests.post(
        f"{SERVICE_URL}/generate", 
        json={
            "user_id": USER_ID,
            "caller_voice_path": blob_path,
            "probability": 0.5,
        }, 
        headers=headers(token), 
        timeout=30 # now this call just returns a job ID, the long processing happens in the background.
    )
    resp.raise_for_status()
    job_id = resp.json()["job_id"]

    # Check if done every 10 seconds, up to 20 minutes ( ETA 10 minutes)
    for _ in range(120): 
        time.sleep(10)
        status = requests.get(f"{SERVICE_URL}/status/{job_id}", headers=headers(token), timeout=30)
        data = status.json()
        if data["status"] == "done":
            print(f"      ✓ Generated")
            print(f"        speaker: {data['speaker']}")
            print(f"        famous_person: {data['famous_person']}")
            print(f"        output_blob: {data['output_blob']}")
            return data["output_blob"]
        if data["status"] == "failed":
            raise RuntimeError(data.get("error"))
    raise TimeoutError("Generation timed out")


def step3_download(token: str, output_file: Path, output_blob: str) -> None:
    """Test: Download finished ringtone from GCS."""
    print(f"\n[3/3] Downloading ringtone ...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    resp = requests.post(
        f"{SERVICE_URL}/download",
        json={"blob_path": output_blob},
        headers=headers(token),
    )
    resp.raise_for_status()
    
    with open(output_file, "wb") as f:
        f.write(resp.content)
    
    size_kb = output_file.stat().st_size / 1024
    print(f"      ✓ Saved to {output_file.name} ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _format_minutes(seconds: float) -> str:
    return f"{seconds / 60:.2f} min"


def run_e2e() -> list[dict]:
    """Run the full e2e test workflow for both .mp3 and .wav files."""
    print(f"\n{'='*60}")
    print(f"End-to-End GCP Deployment Test (All Formats)")
    print(f"{'='*60}")
    print(f"Service URL: {SERVICE_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Test files: {', '.join(f.name for f in TEST_FILES)}")
    
    # Verify all test files exist
    for test_file in TEST_FILES:
        if not test_file.exists():
            raise FileNotFoundError(f"Test file not found: {test_file}")
    
    # Authenticate with GCP
    try:
        token = get_identity_token()
        print(f"✓ Authenticated with GCP\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print(f"\nTo fix:")
        print(f"  Local: gcloud auth application-default login")
        print(f"         gcloud auth print-identity-token")
        print(f"         or set ID_TOKEN in env")
        print(f"  CI/CD: Configure Workload Identity Federation in GitHub Actions")
        raise
    
    results = []
    
    try:
        # Test each file format
        for idx, upload_file in enumerate(TEST_FILES, 1):
            print(f"\n{'─'*60}")
            print(f"Test {idx}/{len(TEST_FILES)}: {upload_file.name}")
            print(f"{'─'*60}")
            
            step0_health(token)
            blob_path = step1_upload(token, upload_file)

            generate_start = time.monotonic()
            output_blob = step2_generate(token, blob_path)
            generate_seconds = time.monotonic() - generate_start
            
            # Save output with unique name (e.g., ringtone_mille.wav, ringtone_viktor.wav)
            file_stem = upload_file.stem  # filename without extension
            output_file = OUTPUT_DIR / f"ringtone_{file_stem}.wav"
            step3_download(token, output_file, output_blob)
            
            results.append({
                "input": upload_file.name,
                "output": output_file.name,
                "status": "✅ passed",
                "generate_minutes": _format_minutes(generate_seconds),
            })
        
        print(f"\n{'='*60}")
        print(f"Test Results")
        print(f"{'='*60}")
        for result in results:
            print(
                f"{result['status']} | {result['input']} → {result['output']} | "
                f"generate: {result['generate_minutes']}"
            )
        print(f"{'='*60}\n")
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Test failed: {e}") from e

    return results


def test_e2e_gcp_deployment():
    """Pytest entrypoint for the e2e workflow."""
    results = run_e2e()
    assert all(result["status"] == "✅ passed" for result in results)


def main():
    run_e2e()


if __name__ == "__main__":
    main()
