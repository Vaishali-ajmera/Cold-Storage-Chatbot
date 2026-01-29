import json
import logging

from chat.constants import (
    CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT,
    CHAT_CLASSIFIER_SYSTEM_PROMPT,
    CHAT_MCQ_GENERATOR_SYSTEM_PROMPT,
    CHAT_META_RESPONSE_SYSTEM_PROMPT,
    CHAT_OUT_OF_CONTEXT_RESPONSE_SYSTEM_PROMPT,
)

logger = logging.getLogger("chat.prompts")


def _get_system_config():
    from accounts.models import SystemConfiguration

    return SystemConfiguration.get_config()


def _get_config_instructions():
    config = _get_system_config()

    if not config:
        return ""

    instructions = []

    tone_map = {
        "friendly": "Be warm, approachable, and conversational. Use friendly language.",
        "professional": "Be professional and businesslike. Maintain formal courtesy.",
        "formal": "Be very formal and respectful. Use polished, official language.",
        "casual": "Be relaxed and casual. Use simple, everyday language.",
    }
    if config.response_tone and config.response_tone in tone_map:
        instructions.append(f"TONE: {tone_map[config.response_tone]}")

    length_map = {
        "concise": "Keep responses SHORT and DIRECT. Maximum 2-3 sentences per point. Avoid unnecessary detail.",
        "moderate": "Provide BALANCED responses. Explain clearly but don't over-elaborate. 3-5 sentences per point.",
        "detailed": "Provide COMPREHENSIVE responses. Include examples, explanations, and helpful context. Be thorough.",
    }
    if config.response_length and config.response_length in length_map:
        instructions.append(f"LENGTH: {length_map[config.response_length]}")

    if config.additional_context and config.additional_context.strip():
        instructions.append(
            f"\nADDITIONAL CONTEXT:\n{config.additional_context.strip()}"
        )

    if config.custom_instructions and config.custom_instructions.strip():
        instructions.append(
            f"\nCUSTOM INSTRUCTIONS:\n{config.custom_instructions.strip()}"
        )

    return "\n".join(instructions)


def _format_history(chat_history: list) -> str:
    if not chat_history:
        return ""

    history_text = "\n\nPREVIOUS CONVERSATION:\n"
    for msg in chat_history:
        history_text += f"{msg['sender'].upper()}: {msg['message']}\n"

    return history_text


def get_classifier_prompt(intake_data: dict, chat_history: list, user_question: str):
    system_prompt = CHAT_CLASSIFIER_SYSTEM_PROMPT
    intake_text = json.dumps(intake_data, indent=2)

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    Classify this question now."""
    logger.info(f"user prompt classifier: {user_prompt}")

    return system_prompt, user_prompt


def get_meta_response_prompt(
    user_question: str, meta_subtype: str, preferred_language: str
):
    system_prompt = CHAT_META_RESPONSE_SYSTEM_PROMPT.replace(
        "{{LANGUAGE}}", preferred_language
    )

    user_prompt = f"""USER QUESTION:
                    "{user_question}"

                    QUESTION TYPE: {meta_subtype}

                    Generate a natural, friendly response in {preferred_language}."""
    logger.info(f"user prompt meta: {user_prompt}")

    return system_prompt, user_prompt


def get_out_of_context_response_prompt(
    user_question: str, out_of_context_type: str, preferred_language: str
):
    system_prompt = CHAT_OUT_OF_CONTEXT_RESPONSE_SYSTEM_PROMPT.replace(
        "{{LANGUAGE}}", preferred_language
    )

    user_prompt = f"""USER QUESTION:
                    "{user_question}"

                    OUT_OF_CONTEXT TYPE: {out_of_context_type}

                    Generate a brief acknowledgment and polite redirect in {preferred_language}."""
    logger.info(f"user prompt out of context: {user_prompt}")

    return system_prompt, user_prompt


def get_mcq_generator_prompt(
    intake_data: dict, user_question: str, missing_field: str, preferred_language: str
):
    system_prompt = CHAT_MCQ_GENERATOR_SYSTEM_PROMPT.replace(
        "{{LANGUAGE}}", preferred_language
    )
    intake_text = json.dumps(intake_data, indent=2)

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}

                    USER'S ORIGINAL QUESTION:
                    "{user_question}"

                    MISSING FIELD TO COLLECT:
                    {missing_field}

                    TARGET LANGUAGE: {preferred_language}

                    Generate an MCQ in {preferred_language} to collect this missing information."""
    logger.info(f"user prompt mcq: {user_prompt}")

    return system_prompt, user_prompt


def get_answer_generator_prompt(
    intake_data: dict,
    chat_history: list,
    user_question: str,
    preferred_language: str,
    mcq_response: str = None,
):
    # Only answer generator uses config instructions
    config_instructions = _get_config_instructions()

    system_prompt = CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT.replace(
        "{{LANGUAGE}}", preferred_language
    )

    # Inject config instructions (tone, length, additional context, custom instructions)
    system_prompt = f"{system_prompt}\n\n{config_instructions}"

    intake_text = json.dumps(intake_data, indent=2)

    mcq_text = ""
    if mcq_response:
        mcq_text = f"\n\nUSER'S MCQ RESPONSE:\n{mcq_response}"

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}
                    {mcq_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    TARGET LANGUAGE: {preferred_language}

                    Provide your answer and suggested follow-up questions in {preferred_language} only."""
    logger.info(f"user prompt answer: {user_prompt}")

    return system_prompt, user_prompt
