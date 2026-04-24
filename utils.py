from pathlib import Path

def get_ringtone_output_path(base_path):
    """Generate the next versioned filename (e.g., ringtone_001.wav, ringtone_002.wav, ...)"""
    base = Path(base_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    
    counter = 1
    while True:
        new_path = f"{base}_{counter:03d}.wav"
        if not Path(new_path).exists():
            return new_path
        counter += 1