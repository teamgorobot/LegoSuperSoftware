SYSTEM_INSTRUCTIONS = (
    "You are a robotics coach and Pybricks engineer for LEGO SPIKE Prime. "
    "Generate reliable, competition-ready plans. "
    "Return only JSON."
)

JSON_SCHEMA = {
    "code": "<pybricks code as a single string>",
    "tutorial": "<step-by-step build tutorial as a single string>"
}


def build_user_prompt(payload: dict) -> str:
    tasks = payload.get("tasks", "").strip()
    notes = payload.get("notes", "").strip()
    parts = payload.get("parts", "").strip()
    constraints = payload.get("constraints", "").strip()
    sensors = payload.get("sensors", "").strip()
    competition = payload.get("competition", "WRO").strip()

    return (
        "Create a Pybricks program and a robot build tutorial for a LEGO "
        f"{competition} competition. Use SPIKE Prime and Pybricks.\n\n"
        "Requirements:\n"
        "- Return ONLY valid JSON with keys: code, tutorial\n"
        "- The code must be complete and runnable\n"
        "- The tutorial must be step-by-step and practical\n"
        "- Assume team has standard SPIKE Prime set unless parts say otherwise\n\n"
        "Inputs:\n"
        f"Tasks/Missions:\n{tasks}\n\n"
        f"Notes/Observations:\n{notes}\n\n"
        f"Available Parts/Hardware:\n{parts}\n\n"
        f"Sensors/Ports/Motors:\n{sensors}\n\n"
        f"Constraints/Rules:\n{constraints}\n\n"
        "Now produce the JSON."
    )
