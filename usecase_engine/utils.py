import json

from decouple import config
from google import genai
from google.genai import types

from usecase_engine.constants import MODEL_NAME, SUGGESTED_QUESTIONS_SYSTEM_PROMPT


def get_suggested_questions_user_prompt(
    user_choice_key, intake_data, preferred_language, original_welcome_message
):
    intent_map = {
        "build": "User Intent: Build a NEW cold storage facility for potato crop.",
        "existing": "User Intent: Optimize an EXISTING cold storage facility for potato crop.",
    }

    intent_desc = intent_map.get(user_choice_key, "User Intent: General inquiry.")

    return f"""
{intent_desc}
PREFERRED LANGUAGE: {preferred_language}

USER INTAKE DATA:
{json.dumps(intake_data, indent=2)}

ORIGINAL WELCOME MESSAGE TO LOCALIZE:
"{original_welcome_message}"

TASK:
1. Translate/Localize the Welcome Message into {preferred_language}.
2. Generate 3 high-impact questions in {preferred_language} that the user would logically ask next based on their intake data.
"""


def generate_localized_onboarding_content(
    user_choice, intake_data, preferred_language, original_welcome
):
    from accounts.constants import LANGUAGE_MAP

    welcome_message = original_welcome
    suggested_questions = []

    language_full_name = LANGUAGE_MAP.get(preferred_language, "English")

    api_key = config("GEMINI_API_KEY", default=None)
    if not api_key:
        return welcome_message, suggested_questions

    try:
        user_input = get_suggested_questions_user_prompt(
            user_choice, intake_data, language_full_name, original_welcome
        )
        client = genai.Client(api_key=api_key)

        system_instruction = SUGGESTED_QUESTIONS_SYSTEM_PROMPT.replace(
            "{{LANGUAGE}}", language_full_name
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_mime_type="application/json",
            ),
            contents=user_input,
        )

        raw_reply = json.loads(response.text)
        if isinstance(raw_reply, dict):
            welcome_message = raw_reply.get("welcome_message", original_welcome)
            suggested_questions = raw_reply.get("suggested_questions", [])

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Gemini generation failed: {e}")

    return welcome_message, suggested_questions
