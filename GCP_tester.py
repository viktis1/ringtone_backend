#!/usr/bin/env python3
"""
Test script for the TTS ringtone generation API on GCP.
Uploads a test voice clip, generates a ringtone, and downloads the result.
"""

import os
import sys
import requests
from pathlib import Path
from google.cloud import storage

# ============================================================================
# Configuration
# ============================================================================

# Cloud Run endpoint (set this to your actual Cloud Run URL)
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "https://create-ringtone-996521322298.europe-west1.run.app")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "contact-info-bucket") # Must match the bucket used by the Cloud Run service
USER_ID = "tester"  # Test user ID

# Local paths
INPUT_FILE = Path("voice_clips_tester/Friends/Mille/mille_high_pitch.mp3")
OUTPUT_DIR = Path("voice_clips_tester/output_GCP")
OUTPUT_FILE = OUTPUT_DIR / "mille_high_pitch.wav"

# ============================================================================
# Helpers
# ============================================================================

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory ready: {OUTPUT_DIR}")

def file_exists(path: Path) -> bool:
    """Check if a file exists."""
    if not path.exists():
        print(f"✗ File not found: {path}")
        return False
    print(f"✓ File found: {path}")
    return True

def upload_to_gcs_via_api(local_path: str, user_id: str, filename: str) -> str:
    """
    Step 1: Get signed upload URL from API, then upload file to GCS.
    Returns the blob path on success.
    """
    print(f"\n--- Step 1: Upload voice clip ---")
    
    # Request signed upload URL
    upload_url_resp = requests.post(
        f"{CLOUD_RUN_URL}/upload-url",
        json={"user_id": user_id, "filename": filename}
    )
    if upload_url_resp.status_code != 200:
        print(f"✗ Failed to get upload URL: {upload_url_resp.status_code}")
        print(f"  Response: {upload_url_resp.text}")
        sys.exit(1)
    
    data = upload_url_resp.json()
    signed_url = data["upload_url"]
    blob_path = data["blob_path"]
    print(f"✓ Got signed upload URL")
    print(f"  Blob path: {blob_path}")
    
    # Upload file to GCS using signed URL
    with open(local_path, "rb") as f:
        file_data = f.read()
    
    upload_resp = requests.put(signed_url, data=file_data)
    if upload_resp.status_code != 200:
        print(f"✗ Failed to upload to GCS: {upload_resp.status_code}")
        print(f"  Response: {upload_resp.text}")
        sys.exit(1)
    
    print(f"✓ Uploaded {len(file_data)} bytes to GCS")
    return blob_path

def generate_ringtone(caller_voice_blob: str, probability: float = 0.5) -> dict:
    """
    Step 2: Call /generate endpoint to synthesize the ringtone.
    Returns response JSON with output_blob path.
    """
    print(f"\n--- Step 2: Generate ringtone ---")
    
    generate_resp = requests.post(
        f"{CLOUD_RUN_URL}/generate",
        json={
            "user_id": USER_ID,
            "caller_voice_blob": caller_voice_blob,
            "probability": probability
        }
    )
    
    if generate_resp.status_code != 200:
        print(f"✗ Failed to generate ringtone: {generate_resp.status_code}")
        print(f"  Response: {generate_resp.text}")
        sys.exit(1)
    
    result = generate_resp.json()
    print(f"✓ Ringtone generated successfully")
    print(f"  Speaker: {result.get('speaker')}")
    print(f"  Famous person: {result.get('famous_person')}")
    print(f"  Output blob: {result.get('output_blob')}")
    
    return result

def download_from_gcs_via_api(user_id: str, filename: str, output_path: Path) -> None:
    """
    Step 3: Get signed download URL from API, then download file from GCS.
    """
    print(f"\n--- Step 3: Download ringtone ---")
    
    # Request signed download URL
    download_url_resp = requests.post(
        f"{CLOUD_RUN_URL}/download-url",
        json={"user_id": user_id, "filename": filename}
    )
    
    if download_url_resp.status_code != 200:
        print(f"✗ Failed to get download URL: {download_url_resp.status_code}")
        print(f"  Response: {download_url_resp.text}")
        sys.exit(1)
    
    data = download_url_resp.json()
    signed_url = data["download_url"]
    print(f"✓ Got signed download URL")
    
    # Download file from GCS using signed URL
    download_resp = requests.get(signed_url)
    if download_resp.status_code != 200:
        print(f"✗ Failed to download from GCS: {download_resp.status_code}")
        sys.exit(1)
    
    # Write to local file
    output_path.write_bytes(download_resp.content)
    print(f"✓ Downloaded {len(download_resp.content)} bytes")
    print(f"  Saved to: {output_path}")

def health_check() -> bool:
    """Check if the API is running."""
    print(f"\n--- Health check ---")
    try:
        resp = requests.get(f"{CLOUD_RUN_URL}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✓ API is healthy")
            return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API is not reachable: {e}")
        return False
    
    return False

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 70)
    print("TTS Ringtone Generation API - GCP Tester")
    print("=" * 70)
    
    print(f"\nConfiguration:")
    print(f"  Cloud Run URL: {CLOUD_RUN_URL}")
    print(f"  GCS Bucket: {GCS_BUCKET}")
    print(f"  User ID: {USER_ID}")
    
    # Health check
    if not health_check():
        print("\n✗ Cannot reach the API. Make sure:")
        print("  1. Cloud Run service is deployed")
        print("  2. CLOUD_RUN_URL is correct")
        print("  3. You have network access to the service")
        sys.exit(1)
    
    # Validate input file
    if not file_exists(INPUT_FILE):
        sys.exit(1)
    
    # Prepare output directory
    ensure_output_dir()
    
    # Run the workflow
    try:
        # Step 1: Upload
        blob_path = upload_to_gcs_via_api(
            str(INPUT_FILE),
            USER_ID,
            "mille_high_pitch.mp3"
        )
        
        # Step 2: Generate
        result = generate_ringtone(blob_path, probability=0.5)
        output_blob = result["output_blob"]
        speaker = result["speaker"]
        
        # Step 3: Download
        download_from_gcs_via_api(
            USER_ID,
            f"{speaker}_ringtone.wav",
            OUTPUT_FILE
        )
        
        print(f"\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print(f"  Output saved to: {OUTPUT_FILE}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
