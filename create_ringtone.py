from sample_speaker import sample_speaker
from generate_script import generate_script
from utils import get_ringtone_output_path
from voxcpm import VoxCPM
import soundfile as sf
import torch
import argparse
from pathlib import Path

torch.set_float32_matmul_precision('high') # Does this do something? Idk what it is

print("torch.cuda.is_available():", torch.cuda.is_available())


def create_ringtone(text, reference_wav_path, output_path, model_path=None):
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
        cache_dir=model_path 
    )

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

