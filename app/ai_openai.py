import base64
import json
import mimetypes
import os
from pathlib import Path

from openai import OpenAI

from prompt_templates import SYSTEM_INSTRUCTIONS, build_user_prompt


def _data_url_for_image(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _extract_output_text(response) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    output = getattr(response, "output", None)
    if isinstance(output, list):
        for item in output:
            item_type = None
            if isinstance(item, dict):
                item_type = item.get("type")
                content = item.get("content", [])
            else:
                item_type = getattr(item, "type", None)
                content = getattr(item, "content", [])

            if item_type == "message":
                for c in content:
                    c_type = c.get("type") if isinstance(c, dict) else getattr(c, "type", None)
                    if c_type == "output_text":
                        return c.get("text") if isinstance(c, dict) else getattr(c, "text", "")

    return str(response)


def generate_with_openai(settings, user_payload, image_paths):
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OpenAI API key is missing. Set it in the app or in OPENAI_API_KEY.")

    client = OpenAI(api_key=api_key)

    user_prompt = build_user_prompt(user_payload)
    content = [{"type": "input_text", "text": user_prompt}]

    if settings.include_images:
        for path in image_paths:
            content.append(
                {
                    "type": "input_image",
                    "image_url": _data_url_for_image(path),
                    "detail": settings.image_detail,
                }
            )

    response = client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": content}],
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
    )

    return _extract_output_text(response)
