# Jetson Orin Onboarding Guide for Robonex AI Voice Control

This guide explains how to deploy the Robonex AI voice-based interaction project on an NVIDIA Jetson Orin for a real quadruped robot.

## 1. Environment Setup

### 1.1 CycloneDDS Installation
CycloneDDS requires careful installation on ARM64 platforms like the Jetson. The repository includes a setup script `cyclonedds_python_setup.sh`. Run this script carefully:

```bash
cd Svan_project1/robonex_ai
chmod +x cyclonedds_python_setup.sh
./cyclonedds_python_setup.sh
```

Ensure `CYCLONEDDS_HOME` is added to your `~/.bashrc` as the script does.
You will also need to source `~/.bashrc` in every new terminal.

### 1.2 Python Dependencies
Make sure you are in the correct Conda environment (or python environment) as configured by the script.

```bash
pip install -r requirements.txt # (if one is provided, otherwise install below)
pip install uvicorn fastapi groq speechrecognition pydantic numpy python-dotenv
```

For SpeechRecognition to access the microphone on the Jetson, you will likely need `pyaudio`:
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

## 2. Hardware Considerations

### Microphone Setup
Ensure your USB or I2S microphone is recognized by ALSA:
```bash
arecord -l
```
You may need to configure the ALSA default device if the Jetson defaults to a dummy audio device.

### Performance Mode
The Jetson Orin should be put in maximum performance mode (MAXN) for lowest latency in DDS and STT/LLM execution:
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

## 3. Transitioning to Edge AI (Local Execution)
Currently, the codebase relies on cloud APIs (`AsyncGroq`) for the LLM and Google's cloud API for Speech-To-Text. For a robust real-world robot, you should run these locally to eliminate network latency and dependency.

### 3.1 Local STT (Whisper)
Replace `recognizer.recognize_google(audio)` in `microphone.py` with a local STT engine like `faster-whisper`, which runs incredibly fast on the Jetson Orin GPU.

### 3.2 Local LLM (Ollama / TensorRT-LLM)
Replace the Groq API call in `brain.py` with a local call.
- Install Ollama on the Jetson.
- Use a small, fast model like `llama3.2:1b` or `phi3`.
- Modify `brain.py` to use the local Ollama endpoint (e.g., `http://localhost:11434/api/generate`) instead of the Groq client.

## 4. Running the Code

1. Ensure the `GROQ_API_KEY` is set in the `.env` file (if still using Groq).
2. Start the main script:
```bash
cd Svan_project1/robonex_ai
python main.py
```
This will start the microphone listening thread, the DDS publisher heartbeat thread, and the FastAPI server.
