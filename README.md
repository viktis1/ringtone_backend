# 📱 Personalized Ringtone Generator

This repository generates and synthesizes custom ringtones personalized to you. Ringtones can be generated either in the voice of your contact person or a famous person (like Trump, Morgan Freeman, Seth Rogan, or David Attenborough).

**Example:**
- Input voice clip: `voice_clips_tester/Friends/Mille/` 
- Generated ringtone: `voice_clips_tester/output/`

## 🔄 Pipeline Architecture

The ringtone generation pipeline is hosted on **Google Cloud Run** with the following workflow:

```
Upload sound file to GCS 
    ↓
API call to Gemini to generate text script 
    ↓
Sample voice (caller or famous person)
    ↓
TTS voice synthesis (VoxCPM2)
    ↓
Download generated ringtone from GCS
```

### Pipeline Flow Details

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

## 🚀 Getting Started

### Prerequisites

- **GPU**: NVIDIA GPU with CUDA 12.2 support (e.g., NVIDIA L4 on GCP)
- **Python**: 3.10
- **System Dependencies**: FFmpeg, build-essential

### Local Installation

```bash
# Clone repository and install dependencies
git clone <repo_url>
cd TTS
pip install -r requirements.txt
```

### Environment Variables

```bash
# For local testing
export GEMINI_API_KEY="your_gemini_api_key"
export GCS_BUCKET="your_gcs_bucket_name"
```

## 💻 Usage

### Generate a Ringtone Locally

```bash
# Using caller voice with 70% probability
python create_ringtone.py \
  --caller_voice tests/fixtures/viktor.wav \
  --probability 0.7 \
  --output voice_clips/output/

# Using only famous person voices
python create_ringtone.py \
  --probability 0.0 \
  --output voice_clips/output/


## 📂 Project Structure

```
TTS/
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

## 🔧 Core Components

### `create_ringtone.py`
- Uses **VoxCPM2** model for voice cloning and synthesis
- Generates `.wav` files with personalized audio

### `generate_script.py`
- Calls **Google Gemini API** to generate scripts
- Creates context-aware text conditioned on speaker identity (and maybe soon deelings and language)

### `sample_speaker.py`
- Randomly samples speakers based on probability distribution
- Supports caller voice cloning, fallback to famous person voices

### `main.py`
- FastAPI service for cloud deployment
- Handles file uploads/downloads from GCS
- Manages async ringtone generation jobs

## ☁️ Cloud Deployment (GCP)

### Cloud Run Setup
- **Region**: europe-west1
- **Memory**: 24GB
- **CPU**: 6 cores
- **GPU**: NVIDIA L4 (1x)
- **Timeout**: 3600 seconds (1 hour)

### CI/CD Pipeline
- GitHub Actions automatically builds and pushes to GHCR
- Deploys to Cloud Run staging/production on main branch
- Runs test suite before production deployment

See `.github/workflows/docker_image_GHCR.yml` for details.

## 🧪 Testing

```bash
# Run test suite
pytest tests/ -v

# Run specific test
pytest tests/test_e2e_gcp_deployment.py -v
```

## 📋 TODO & Future Enhancements

- [ ] **KGE Exploration**: Explore hosting on GKE instead of Cloud Run
  - [ ] Price comparison (free tier covers cluster management)
  - [ ] Evaluate GPU requirements vs Cloud Run
  
- [ ] **Emotion Detection**: Implement a feeling detector
  - Analyze input voice clip to detect emotion
  - Generate scripts that match the detected mood
  
- [ ] **Language Detection**: Auto-detect language of input voice
  - Generate scripts in the same language as the voice clip. VOXCPM2 can handle cross-lingual gneration, but I think it is worse. 

- [ ] **Per-User GCS Buckets**: Implement user-scoped storage

## 🛠️ Technologies

- **TTS Model**: [VoxCPM2](https://github.com/openbmb/VoxCPM2) - Voice cloning and synthesis
- **LLM**: Google Gemini API - Script generation
- **Backend**: FastAPI + Uvicorn
- **Cloud**: Google Cloud Run + Cloud Storage
- **GPU**: NVIDIA L4 with CUDA 12.2
- **Container**: Docker

## 📝 License

See [LICENSE](LICENSE) file for details.

## 👤 Author

Created by Viktor Isaksen

---

**Questions or contributions?** Shoot me an email: isaksenviktor@gmail.com
