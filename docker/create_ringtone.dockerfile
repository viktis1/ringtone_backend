FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for audio processing and PyTorch
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY create_ringtone.py .
COPY sample_speaker.py .
COPY generate_script.py .
COPY utils.py .

# Copy voice clips (famous people only)
COPY voice_clips/david_attenborough ./voice_clips/david_attenborough
COPY voice_clips/morgan_freeman ./voice_clips/morgan_freeman
COPY voice_clips/seth_rogan ./voice_clips/seth_rogan
COPY voice_clips/Trump ./voice_clips/Trump

# Create directory for runtime mount
RUN mkdir -p /app

ENTRYPOINT ["python", "create_ringtone.py"]
