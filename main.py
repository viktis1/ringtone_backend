from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from sample_speaker import sample_speaker
from generate_script import generate_script
from create_ringtone import create_ringtone
from utils import get_ringtone_output_path
import torch

app = FastAPI()

class RingtoneRequest(BaseModel):
    caller_voice: str = None
    probability: float = 0.5
    output: str = None

@app.post("/generate")
async def generate_ringtone_endpoint(request: RingtoneRequest):
    try:
        # Validate probability
        if not 0.0 <= request.probability <= 1.0:
            raise HTTPException(status_code=400, detail="Probability must be between 0.0 and 1.0")
        
        # Validate caller voice file if provided
        if request.caller_voice:
            caller_path = Path(request.caller_voice)
            if not caller_path.exists():
                raise HTTPException(status_code=400, detail=f"Caller voice file not found: {request.caller_voice}")
            caller_speech = str(caller_path)
        else:
            caller_speech = False
        
        # Sample speaker
        speaker, famous_person, voice_path = sample_speaker(p=request.probability, caller_speech=caller_speech)
        
        # Generate script
        script = generate_script(receiver="Viktor", caller="Mille", speaker=speaker, famous_person=famous_person)
        
        # Create ringtone
        output_root = Path(request.output) if request.output else Path("voice_clips/output")
        output_path = Path(get_ringtone_output_path(str(output_root / speaker / "ringtone")))
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        create_ringtone(
            text=script,
            reference_wav_path=voice_path,
            output_path=str(output_path)
        )
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "speaker": speaker,
            "famous_person": famous_person
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
