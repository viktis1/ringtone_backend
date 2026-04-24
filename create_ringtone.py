from sample_speaker import sample_speaker
from generate_script import generate_script
from utils import get_ringtone_output_path
from voxcpm import VoxCPM
import soundfile as sf
import torch

torch.set_float32_matmul_precision('high') # Does this do something? Idk what it is

print("torch.cuda.is_available():", torch.cuda.is_available())


def create_ringtone(text, reference_wav_path, output_path):
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
    )

    wav = model.generate(
        text=text,
        reference_wav_path=reference_wav_path,
    )
    sf.write(output_path, wav, model.tts_model.sample_rate)
    
if __name__ == "__main__":
    # Start by sampling a speaker
    speaker, famous_person, voice_path = sample_speaker(p=0.5, caller_speech=False) # TODO: find out how to use caller speech
    # Then generate a script for the ringtone
    script = generate_script(receiver="Viktor", caller="Mille", speaker=speaker, famous_person=famous_person)
    # Finally, create the ringtone using the generated script and the speaker's voice clip
    output_path = get_ringtone_output_path(f"voice_clips/output/{speaker}/ringtone")
    create_ringtone(
        text=script, 
        reference_wav_path=voice_path, 
        output_path=output_path
        )

