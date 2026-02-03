from prompt_templates import SYSTEM_INSTRUCTIONS, build_user_prompt


def generate_with_local(settings, user_payload):
    if not settings.local_model_path:
        raise ValueError("Local model path is empty. Please select a .gguf model file.")

    try:
        from llama_cpp import Llama
    except Exception as exc:
        raise RuntimeError(
            "llama-cpp-python is not installed. Install it to use local AI."
        ) from exc

    prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"{build_user_prompt(user_payload)}\n\n"
        "Return ONLY JSON with keys code and tutorial."
    )

    llm = Llama(model_path=settings.local_model_path, n_ctx=4096)
    result = llm.create_completion(
        prompt=prompt,
        max_tokens=settings.max_output_tokens,
        temperature=settings.temperature,
    )

    choices = result.get("choices", [])
    if not choices:
        return ""

    return choices[0].get("text", "")
