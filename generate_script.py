import requests


def generate_script(receiver, caller, speaker, feeling=None, famous_person=True):
    url = "http://localhost:11434/api/generate"

    if feeling is not None:
        feeling_prompt = f" The emotion of the speaker should be {feeling}."
    else:
        feeling_prompt = ""
    
    if famous_person == True:
        famous_person_prompt = (
            f"The script will be read out by {speaker}. You should write the script in a way that "
            f"matches the speaking style of {speaker}. The narration should be in 3rd person, as the "
            f"speaker ({speaker}) is narrating the situation of {caller} calling {receiver}."
        )
    else:
        famous_person_prompt = (
            f"The script will be read out by the caller ({caller}) of the phone call. The narration should "
            f"be in 1st person, as the speaker ({caller}) is narrating the situation of {caller} calling {receiver}."
        )

    prompt = (
        "I am writing small cute scripts for ringtones and then getting a TTS model to read them with "
        "the voices. Can you generate a new small messages? Your answer should contain nothing but the "
        "text that should be read out. The call should be kind of meta talking about the call itself and "
        "the fact that the person is calling. The script should be around 100 words. The script should also "
        "be read out to the person who is receiving the call, so it should be written in a way that makes "
        "sense for the receiver. The script should also mention the name of the caller ({caller}) and the "
        f"receiver ({receiver}). However, the inclusion of the names should be natural and not forced."
    )
    
    payload = {
        "model": "qwen3.5:9b",   # pick from ["qwen3.6", "medgemma1.5", "glm-5.1"]
        "prompt":  prompt + feeling_prompt + famous_person_prompt,
        "stream": False
    }
    # print(prompt + feeling_prompt + famous_person_prompt)

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    return data["response"]




if __name__ == "__main__":
    
    answer = generate_script("Viktor", "Mille", "Trump")
    print(answer)