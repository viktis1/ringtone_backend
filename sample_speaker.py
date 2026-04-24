""" This script will sample the speaker from available speakers. It accepts 
a probability (p) for using the callers voice clip and generates a random number (r)
- if r < p: use caller voice clips
- else: use famous persons voice clip to narrate the situation of getting a phone call.

Later I want to implement a model that classifies the voice emotion. The emotion of the 
speaker in the voice clip will be used to generate a script that matches the emotion. """

from pathlib import Path
import random


def _audio_files_in_dir(folder: Path):
    files = []
    for path in folder.iterdir():
        if path.is_file() and path.suffix.lower() in {".wav", ".mp3"}:
            files.append(path)
    return files


def sample_speaker(p=0.5, voice_clips_dir="voice_clips", exclude=("Friends", "output", "caller"), caller_speech = False):
    if random.random() < p and caller_speech: # only use caller voice if a clip is available (caller_speech=path).
        person = "caller"
        famous_person = False
        voice_path = caller_speech  # Use the provided caller voice path

    else:
        base_dir = Path(__file__).resolve().parent / voice_clips_dir
        people = []
        audio_files_by_person = {}
        exclude_set = set(exclude)

        for folder in base_dir.iterdir():
            if not folder.is_dir() or folder.name in exclude_set:
                continue
            audio_files = _audio_files_in_dir(folder)
            if audio_files:
                people.append(folder.name)
                audio_files_by_person[folder.name] = audio_files

        if not people:
            raise RuntimeError(f"No usable audio clips found in {base_dir}. Add .wav or .mp3 files.")

        person = random.choice(people)
        famous_person = True
        audio_files = audio_files_by_person[person]
        voice_path = random.choice(audio_files)

    return person, famous_person, voice_path

if __name__ == "__main__":
    for _ in range(10):
        print(sample_speaker(p=0.0))