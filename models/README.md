# Local model files

Place your local `.gguf` model files in this folder (or anywhere else) and select the file path in the app.

Recommended sizes:
- 7B or 8B models for faster generation
- 13B+ models for higher quality (bigger and slower)

## Multi-model offline mode
The app supports a "local_multi" mode with three models:
- Code model (e.g. Qwen3 Coder GGUF)
- Tutorial model (e.g. Mistral GGUF)
- Image model (vision-capable GGUF)

For image analysis, use a LLaVA-style vision GGUF. If your model needs a
`.mmproj` file, place it next to the model. The app will auto-detect it.

Example pairing:
- `qwen3-coder*.gguf` for code
- `mistral*.gguf` for tutorial
- `inyblip*.gguf` (vision) for image analysis
