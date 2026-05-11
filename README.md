# 📱 Personalized Ringtone Generator

This repository generates and synthesizes custom ringtones personalized to you. Ringtones can be generated either in the voice of your contact person or a famous person (like Trump, Morgan Freeman, Seth Rogan, or David Attenborough).

**Example:**
- Input voice clip: `voice_clips_tester/Friends/Mille/` 
- Generated ringtone: `voice_clips_tester/output/`

## 🔄 Pipeline Architecture

The ringtone generation pipeline is hosted on **Google Cloud Run** with the following workflow:


1. **Voice Upload**: Upload an audio sample (`.wav` or `.mp3`) to Google Cloud Storage
2. **Script Generation**: Gemini API generates a personalized script conditioned on:
   - Speaker identity (caller or famous person)
   - Speaker style/tone
   - Names of caller and receiver
3. **Speaker Sampling**: Randomly select between:
   - **Caller mode** (probability `p`): Use the uploaded voice clip
   - **Famous person mode** (probability `1-p`): Use a pre-recorded voice from the `voice_clips/` directory
4. **Voice Synthesis**: VoxCPM2 model generates audio from the script using the selected voice as reference
5. **Output**: Ringtone is saved to GCS and downloaded locally

The code is set up for deployment on Google Cloud Run but the generation (step 2, 3 and 4) can be run locally as well. Text generation (step 2) is set up via Gemini API to reduce latency and docker image size, but for local development, I use ollama for local language models.

### System

- **GPU**: NVIDIA GPU with CUDA 12.2 support (e.g., NVIDIA L4 on GCP and RTX 4090 for local dev)
- **Python**: 3.10 (matching what we deploy to Cloud with)
- **OS** Ubuntu 24.04


## 🚀 Getting Started

### Local Installation

```bash
# Clone repository and install dependencies
git clone https://github.com/viktis1/ringtone_backend
cd ringtone_backend
conda create -n ringtone python=3.10
sudo apt install ffmpeg, build-essential
pip install -r requirements.txt
```

### Generate a Ringtone Locally

```bash
# Using caller voice with 70% probability
python create_ringtone.py \
  --caller_voice tests/fixtures/viktor.wav \
  --probability 0.7 \
  --output voice_clips/output/
```



## ☁️ Cloud Deployment (GCP)


### CI/CD Pipeline
- GitHub Actions automatically builds and pushes to GHCR and creates remote repository on Google Artifact Registry (GHCR hosts for free)
- Deploys to Cloud Run staging on main branch
- Runs test suite before production deployment
- if tests work, push to production

See `.github/workflows/docker_image_GHCR.yml` for more details and the specific Cloud Run setup.

## 🧪 Testing
Testing works locally and in CI
```bash
# Run test suite
pytest tests/ -v
```

## 📋 TODO & Future Enhancements

- [ ] **GKE Exploration**: Explore hosting on GKE instead of Cloud Run
  - [ ] Price comparison (free tier covers cluster management)
  - [ ] Evaluate GPU requirements vs Cloud Run
  
- [ ] **Emotion Detection**: Implement a feeling detector
  - Analyze input voice clip to detect emotion
  - Generate scripts that match the detected mood
  
- [ ] **Language Detection**: Auto-detect language of input voice
  - Generate scripts in the same language as the voice clip. VOXCPM2 can handle cross-lingual gneration, but I think it is worse. 

- [ ] **Per-User GCS Buckets**: Implement user-scoped storage



## 📂 Project Structure

```bash
TTS
├── main.py                    # FastAPI backend
├── create_ringtone.py         # TTS synthesis using VoxCPM2
├── generate_script.py         # Script generation via Gemini API
├── sample_speaker.py          # Voice sampling logic
├── utils.py                   # Utility functions
├── requirements.txt           # Python dependencies
├── docker/
│   └── create_ringtone.dockerfile  # Docker image for Cloud Run
├── voice_clips/               # Pre-recorded voice samples
│   ├── david_attenborough/
│   ├── morgan_freeman/
│   ├── seth_rogan/
│   ├── Trump/
│   └── output/
├── tests/                     # Test suite
│   ├── test_e2e_gcp_deployment.py
│   └── fixtures/
└── weights/                   # VoxCPM2 model cache
```

## 🛠️ SHOUTOUT

- **TTS Model**: [VoxCPM2](https://github.com/OpenBMB/VoxCPM) - Voice cloning and synthesis
- **LLM**: Google Gemini API - Script generation
- **Backend**: FastAPI + Uvicorn
- **Cloud**: Google Cloud Run + Cloud Storage
- **Container**: Docker and GitHub Container Registry

## 📝 License

See [LICENSE](LICENSE) file for details.

## 👤 Author

Created by Viktor Isaksen

---

**Questions or contributions?** Shoot me an email: isaksenviktor@gmail.com
