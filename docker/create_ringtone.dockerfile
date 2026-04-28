FROM nvidia/cuda:13.0.3-cudnn-runtime-ubuntu24.04


# Install system dependencies and python
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.12 /usr/bin/python

WORKDIR /app

# Copy requirements and install dependencies. Without --break-system-packages, I get an error with this base image...
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt 

# Copy application code
COPY main.py .
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

# Expose port 8080 for Cloud Run
EXPOSE 8080
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
