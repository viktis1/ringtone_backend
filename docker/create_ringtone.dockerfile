# My local OS is 24.04, but nvidia-l4 only supports CUDA 12.2 and there is no base image from nvidia with CUDA 12.2 and Ubuntu 24.04.
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04 



# Install system dependencies and python
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 

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
