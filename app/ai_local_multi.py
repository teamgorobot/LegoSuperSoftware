from __future__ import annotations

import json
from pathlib import Path

from prompt_templates import SYSTEM_INSTRUCTIONS, build_user_prompt


def _require_llama_cpp():
    try:
        from llama_cpp import Llama  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime import error path
        raise RuntimeError(
            "llama-cpp-python is not installed. Install it to use local AI."
        ) from exc
    return Llama


def _load_text_model(model_path: str):
    Llama = _require_llama_cpp()
    return Llama(model_path=model_path, n_ctx=4096)


def _guess_mmproj_path(model_path: str) -> str | None:
    path = Path(model_path)
    if not path.exists():
        return None

    candidates = [
        path.with_suffix(".mmproj.gguf"),
        path.with_suffix(".mmproj"),
        path.with_name(f"{path.stem}.mmproj.gguf"),
        path.with_name(f"{path.stem}.mmproj"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _analyze_images_with_local(settings, image_paths: list[str]) -> str:
    if not image_paths:
        return ""

    if not settings.local_image_model_path:
        return ""

    try:
        from llama_cpp.llava_cpp import Llava15ChatHandler  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Image analysis requires llama-cpp-python built with vision support "
            "(LLaVA-style). Install/upgrade it or use OpenAI for images."
        ) from exc

    Llama = _require_llama_cpp()
    mmproj_path = _guess_mmproj_path(settings.local_image_model_path)
    if not mmproj_path:
        raise RuntimeError(
            "Image model needs a corresponding mmproj file. "
            "Place a .mmproj(.gguf) next to the image model."
        )

    chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
    llm = Llama(model_path=settings.local_image_model_path, chat_handler=chat_handler, n_ctx=4096)

    summaries = []
    for path in image_paths:
        prompt = (
            "Describe the LEGO robotics scene in this photo. "
            "Focus on missions, field elements, robot configuration, and sensors."
        )
        image_url = Path(path).absolute().as_uri()
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ]
        )
        content = ""
        if response and isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
        if content:
            summaries.append(f"{Path(path).name}: {content}")

    return "\n".join(summaries)


def _generate_text(llm, prompt: str, max_tokens: int, temperature: float) -> str:
    result = llm.create_completion(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    choices = result.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("text", "")


def _parse_model_output(text: str) -> dict:
    if not text:
        return {"code": "", "tutorial": ""}

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            pass

    return {"code": cleaned, "tutorial": ""}


def generate_with_local_multi(settings, user_payload, image_paths: list[str]) -> str:
    if not settings.local_code_model_path:
        raise ValueError("Local code model path is empty.")
    if not settings.local_tutorial_model_path:
        raise ValueError("Local tutorial model path is empty.")

    image_notes = _analyze_images_with_local(settings, image_paths)
    if image_notes:
        user_payload = dict(user_payload)
        extra = user_payload.get("notes", "")
        user_payload["notes"] = f"{extra}\n\nImage observations:\n{image_notes}".strip()

    user_prompt = build_user_prompt(user_payload)
    base_prompt = f"{SYSTEM_INSTRUCTIONS}\n\n{user_prompt}\n\nReturn ONLY JSON with keys code and tutorial."

    code_llm = _load_text_model(settings.local_code_model_path)
    tutorial_llm = _load_text_model(settings.local_tutorial_model_path)

    code_prompt = (
        f"{base_prompt}\n\n"
        "You are the code specialist. Return ONLY JSON with key code and an empty tutorial."
    )
    tutorial_prompt = (
        f"{base_prompt}\n\n"
        "You are the tutorial specialist. Return ONLY JSON with key tutorial and an empty code."
    )

    code_text_raw = _generate_text(code_llm, code_prompt, settings.max_output_tokens, settings.temperature)
    tutorial_text_raw = _generate_text(
        tutorial_llm, tutorial_prompt, settings.max_output_tokens, settings.temperature
    )

    code_data = _parse_model_output(code_text_raw).get("code", "")
    tutorial_data = _parse_model_output(tutorial_text_raw).get("tutorial", "")
    return json.dumps({"code": code_data, "tutorial": tutorial_data})
