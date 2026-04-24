from voxcpm import VoxCPM
import soundfile as sf
import torch

model = VoxCPM.from_pretrained(
  "openbmb/VoxCPM2",
  load_denoiser=False,
)

torch.set_float32_matmul_precision('high') # Does this do something? Idk what it is

# David Attenborough
wav = model.generate(
    text="Greetings! A most fascinating story is unfolding right in front of our eyes. Today, 'Mille, is making a rare " \
    "call to her mate, 'Viktor. The reasons for such an extraordinary communication could range from the mundane to " \
    "the life-altering, but one thing is certain: if Viktor does not answer in time, the details of this significant " \
    "event may be lost forever.",
    reference_wav_path="voice_clips/david_attenborough/Voicy_The conditions are changing fast.mp3",
)
sf.write("voice_clips/david_attenborough.wav", wav, model.tts_model.sample_rate)

# Trump
wav = model.generate(
    text="Hey there! This is a huge deal, folks—a truly enormous call coming in from 'Mille.' " \
    "I've never seen anything like it, and let me tell you, this could be massive! " \
    "Now, I don't want to speculate too much, but Mille is calling about something that might just change " \
    "the game for both of you. It could be a business opportunity, a family emergency, or even a surprise dinner " \
    "reservation. who knows? But one thing is clear: this call requires your immediate attention!",
    reference_wav_path="voice_clips/Trump/Voicy_Politicians are all talk no action nothing is going to .mp3",
)
sf.write("voice_clips/trump.wav", wav, model.tts_model.sample_rate)

# Friends
wav = model.generate(
    text="Hey viktor, kan du lige tage telefonen? Jeg har noget virkelig vigtigt at fortælle dig. Jeg ved, du er" \
    "den sejeste mand i hele verden, men jeg har brug for at tale med dig om noget, der ikke kan vente. Det handler om vores planer for weekenden, og jeg vil bare sikre mig, at vi er på samme side. Så vær sød at svare, når du ser det. Tak!" \
    "Og hvis du ikke svarer, så må jeg bare blive ved med at ringe, indtil du gør det. Jeg mener, det er ikke som om, jeg har noget bedre at lave, vel? Så vær sød at tage telefonen og lad os tale om vores weekendplaner. Jeg lover, det ikke vil tage lang tid, og det vil være det værd.",
    reference_wav_path="voice_clips/Friends/magnus.wav",
    inference_timesteps=30,
)
sf.write("voice_clips/magnus.wav", wav, model.tts_model.sample_rate)

wav = model.generate(
    text="Hey viktor. Can you please pick up the phone? I have something really important to tell you. I know you're busy, but this is something that can't wait. It's about our plans for the weekend, and I need to make sure we're on the same page. So please, just answer the call when you see it. Thanks!" \
    "And if you don't answer, I'll just have to keep calling until you do. I mean, it's not like I have anything better to do, right? So please, just pick up the phone and let's talk about our weekend plans. I promise it won't take long, and it'll be worth it. Thanks again!",
    reference_wav_path="voice_clips/Friends/martiny.wav",
    inference_timesteps=30,
)
sf.write("voice_clips/martiny.wav", wav, model.tts_model.sample_rate)

wav = model.generate(
    text="Hey viktor, kan du lige tage telefonen? Jeg har noget virkelig vigtigt at fortælle dig. Jeg ved, du er" \
    "den sejeste mand i hele verden, men jeg har brug for at tale med dig om noget, der ikke kan vente. Det handler om vores planer for weekenden, og jeg vil bare sikre mig, at vi er på samme side. Så vær sød at svare, når du ser det. Tak!" \
    "Og hvis du ikke svarer, så må jeg bare blive ved med at ringe, indtil du gør det. Jeg mener, det er ikke som om, jeg har noget bedre at lave, vel? Så vær sød at tage telefonen og lad os tale om vores weekendplaner. Jeg lover, det ikke vil tage lang tid, og det vil være det værd.",
    reference_wav_path="voice_clips/Friends/viktor_dansk.wav",
    inference_timesteps=30,
)
sf.write("voice_clips/viktor_dansk.wav", wav, model.tts_model.sample_rate)

wav = model.generate(
    text="Hey viktor. Can you please pick up the phone? I have something really important to tell you. I know you're busy, but this is something that can't wait. It's about our plans for the weekend, and I need to make sure we're on the same page. So please, just answer the call when you see it. Thanks!" \
    "And if you don't answer, I'll just have to keep calling until you do. I mean, it's not like I have anything better to do, right? So please, just pick up the phone and let's talk about our weekend plans. I promise it won't take long, and it'll be worth it. Thanks again!",
    reference_wav_path="voice_clips/Friends/viktor_english.wav",
    inference_timesteps=30,
)
sf.write("voice_clips/viktor_english.wav", wav, model.tts_model.sample_rate)


