import os
from google import genai


def generate_script(receiver, caller, speaker, feeling=None, famous_person=True):
    # Configure Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)

    if feeling is not None:
        feeling_prompt = f"The emotion of the speaker should be {feeling}.\n"
    else:
        feeling_prompt = ""
    
    if famous_person == True:
        narrator_instruction = (
            f"The script is narrated by {speaker} in 3rd person.\n"
            f"{speaker} should narrate {caller} calling {receiver}.\n"
            f"Match {speaker}'s speaking style and mannerisms."
        )
    else:
        narrator_instruction = (
            f"The script is narrated by {caller} (the caller) in 1st person.\n"
            f"{caller} describes their situation calling {receiver}."
        )

    prompt = (
        "You are a ringtone script writer. Generate a short, cute phone call script.\n\n"
        "CONTEXT:\n"
        f"- Caller: {caller}\n"
        f"- Receiver: {receiver}\n"
        f"- Narrator/Voice: {speaker}\n\n"
        "INSTRUCTIONS:\n"
        f"- Output ONLY the script text (nothing else)\n"
        f"- The script is meta - it discusses the call itself and the fact that someone is calling\n"
        f"- Include the caller's name ({caller}) and receiver's name ({receiver}) naturally in the dialogue\n"
        f"- Keep it around 100 words\n"
        f"- Write it to be heard by the receiver ({receiver})\n"
        f"{feeling_prompt}"
        f"NARRATOR:\n"
        f"{narrator_instruction}"
    )
    
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    return response.text




if __name__ == "__main__":
    
    answer = generate_script("Viktor", "Mille", "Trump")
    print(answer)