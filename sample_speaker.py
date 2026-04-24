""" This script will sample the speaker from available speakers. It accepts 
a probability (p) for using the callers voice clip and generates a random number (r)
- if r < p: use caller voice clips
- else: use famous persons voice clip to narrate the situation of getting a phone call.

Later I want to implement a model that classifies the voice emotion. The emotion of the 
speaker in the voice clip will be used to generate a script that matches the emotion. """

from pathlib import Path
import random


def sample_speaker(p=0.5, voice_clips_dir="voice_clips", exclude=("Friends",), caller_speech = False):
    if random.random() < p and caller_speech: # only use caller voice if a clip is available (caller_speech=wav contents).
        person = "caller"
        famous_person = False
        voice_path = None # TODO: find out how to use caller speech

    else:
        base_dir = Path(__file__).resolve().parent / voice_clips_dir
        people = [
            folder.name
            for folder in base_dir.iterdir()
            if folder.is_dir() and folder.name not in set(exclude)
        ]
        person = random.choice(people)
        famous_person = True
        audio_files = list((base_dir / person).glob("*.wav")) + list((base_dir / person).glob("*.mp3"))
        voice_path = random.choice(audio_files)

    return person, famous_person, voice_path

if __name__ == "__main__":
    for _ in range(10):
        print(sample_speaker(p=0.0))