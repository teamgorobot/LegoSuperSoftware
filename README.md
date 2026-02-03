# LegoSuperSoftware

A portable Windows app for LEGO robotics competitions (WRO, FIRST LEGO League) that turns photos + notes into:
- Pybricks code for SPIKE Prime
- A step-by-step build tutorial

## Features
- Hybrid AI mode: OpenAI API or local model (`.gguf`) you choose
- Offline multi-model mode (code + tutorial + image analysis)
- Image + notes input
- One-click copy for code and tutorial
- Offline mode supported with local model file

## Quick start (dev)
1. Create a virtualenv
2. Install dependencies:
   `pip install -r requirements.txt`
3. Run:
   `python app\main.py`

## Build a portable .exe
Use the provided PowerShell script:
`./build_exe.ps1`

Notes:
- For local/offline AI, place a `.gguf` model file and set its path in the app.
- For local multi-model AI, set separate paths for code/tutorial/image models.
- If you plan to use local AI in the .exe, install `llama-cpp-python` before building.
- Image analysis expects a vision-capable GGUF (LLaVA-style). If required, keep the `.mmproj` file next to the image model.

## API key safety
The app lets you paste an OpenAI API key. You can choose whether to remember it on this PC.

## Repo structure
- `app/` main app code
- `models/` local model notes and placeholder
- `build_exe.ps1` PyInstaller script
- `requirements.txt`
