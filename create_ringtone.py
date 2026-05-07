from sample_speaker import sample_speaker
from generate_script import generate_script
from utils import get_ringtone_output_path
from voxcpm import VoxCPM
import soundfile as sf
import torch
import argparse
from pathlib import Path
import tempfile
import os
from google.cloud import storage

torch.set_float32_matmul_precision('high') # Does this do something? Idk what it is

print("torch.cuda.is_available():", torch.cuda.is_available())


def _get_model_cache_dir(gcs_model_path: str) -> str:
    """
    Download model weights from GCS to a local cache directory.
    If weights don't exist in GCS yet, they will be downloaded from Hugging Face
    and uploaded to GCS for future use.
    
    Args:
        gcs_model_path: GCS path like "bucket-name/weights/VoxCPM2"
    
    Returns:
        Local filesystem path to the cached model directory
    """
    if gcs_model_path is None:
        return None
    
    # Use a persistent local cache in /tmp (mounted volume in production)
    local_cache_dir = "/tmp/model_cache"
    os.makedirs(local_cache_dir, exist_ok=True)
    
    try:
        # Try to download existing weights from GCS
        bucket_name, model_prefix = gcs_model_path.split('/', 1)
        gcs = storage.Client()
        bucket = gcs.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=model_prefix))
        
        if blobs:
            print(f"Found {len(blobs)} files in GCS at {gcs_model_path}, downloading...")
            for blob in blobs:
                # Create local path maintaining GCS structure
                relative_path = blob.name[len(model_prefix):].lstrip('/')
                local_file_path = os.path.join(local_cache_dir, relative_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                print(f"  Downloading {blob.name}...")
                blob.download_to_filename(local_file_path)
            print("Model weights downloaded from GCS successfully")
            return local_cache_dir
    except Exception as e:
        print(f"Warning: Could not download from GCS ({e}). Will download from Hugging Face instead.")
    
    # If GCS download failed or no weights in GCS, download from Hugging Face
    print("Downloading model from Hugging Face...")
    return local_cache_dir


def _upload_model_to_gcs(local_cache_dir: str, gcs_model_path: str) -> None:
    """
    Upload downloaded model weights from local cache to GCS.
    
    Args:
        local_cache_dir: Local filesystem path containing the model
        gcs_model_path: GCS path like "bucket-name/weights/VoxCPM2"
    """
    if gcs_model_path is None or not os.path.exists(local_cache_dir):
        return
    
    try:
        bucket_name, model_prefix = gcs_model_path.split('/', 1)
        gcs = storage.Client()
        bucket = gcs.bucket(bucket_name)
        
        print(f"Uploading model to GCS at {gcs_model_path}...")
        for root, dirs, files in os.walk(local_cache_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_file_path, local_cache_dir)
                gcs_file_path = f"{model_prefix}/{relative_path}"
                
                blob = bucket.blob(gcs_file_path)
                print(f"  Uploading {gcs_file_path}...")
                blob.upload_from_filename(local_file_path)
        print("Model weights uploaded to GCS successfully")
    except Exception as e:
        print(f"Warning: Could not upload model to GCS ({e}). Continuing anyway...")


def create_ringtone(text, reference_wav_path, output_path, model_path=None):
    # Get or download model to local cache
    local_cache_dir = _get_model_cache_dir(model_path)
    
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
        cache_dir=local_cache_dir
    )


    # Upload to GCS for future requests (background upload)
    if model_path:
        _upload_model_to_gcs(local_cache_dir, model_path)

    wav = model.generate(
        text=text,
        reference_wav_path=reference_wav_path,
    )
    sf.write(output_path, wav, model.tts_model.sample_rate)
    print(f"Ringtone saved to: {output_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a ringtone with TTS")
    parser.add_argument("--caller_voice", "-c", type=str, default=None,
                        help="Path to caller voice clip (.wav or .mp3)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Base output directory (replaces 'voice_clips/output')")
    parser.add_argument("--probability", "-p", type=float, default=0.5,
                        help="Probability of using caller voice (0.0=only famous, 1.0=only caller, 0.5=mix)")
    args = parser.parse_args()
    
    # Validate probability
    if not 0.0 <= args.probability <= 1.0:
        raise ValueError("Probability must be between 0.0 and 1.0")
    
    # Validate caller voice file if provided
    if args.caller_voice:
        caller_path = Path(args.caller_voice)
        if not caller_path.exists():
            raise FileNotFoundError(f"Caller voice file not found: {args.caller_voice}")
        caller_speech = str(caller_path)
    else:
        caller_speech = False
    
    # Start by sampling a speaker
    speaker, famous_person, voice_path = sample_speaker(p=args.probability, caller_speech=caller_speech)
    # Then generate a script for the ringtone
    script = generate_script(receiver="Viktor", caller="Mille", speaker=speaker, famous_person=famous_person)
    # Finally, create the ringtone using the generated script and the speaker's voice clip
    output_root = Path(args.output) if args.output else Path("voice_clips/output")
    output_path = get_ringtone_output_path(str(output_root / speaker / "ringtone"))
    
    create_ringtone(
        text=script, 
        reference_wav_path=voice_path, 
        output_path=output_path
        )

