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
    # History disabled for now to reduce token usage
    # history_text = _format_history(chat_history)

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    Classify this question now."""
    logger.info(f"user prompt classifier: {user_prompt}")

    return system_prompt, user_prompt


def get_meta_response_prompt(user_question: str, meta_subtype: str, language: str):
    system_prompt = CHAT_META_RESPONSE_SYSTEM_PROMPT

    user_prompt = f"""USER QUESTION:
                    "{user_question}"

                    QUESTION TYPE: {meta_subtype}
                    USER LANGUAGE: {language}

                    Generate a natural, friendly response."""
    logger.info(f"user prompt meta: {user_prompt}")

    return system_prompt, user_prompt


def get_out_of_context_response_prompt(user_question: str, out_of_context_type: str, language: str):
    system_prompt = CHAT_OUT_OF_CONTEXT_RESPONSE_SYSTEM_PROMPT

    user_prompt = f"""USER QUESTION:
                    "{user_question}"

                    OUT_OF_CONTEXT TYPE: {out_of_context_type}
                    USER LANGUAGE: {language}

                    Generate a brief acknowledgment and polite redirect."""
    logger.info(f"user prompt out of context: {user_prompt}")

    return system_prompt, user_prompt


def get_mcq_generator_prompt(intake_data: dict, user_question: str, missing_field: str):
    system_prompt = CHAT_MCQ_GENERATOR_SYSTEM_PROMPT
    intake_text = json.dumps(intake_data, indent=2)

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}

                    USER'S ORIGINAL QUESTION:
                    "{user_question}"

                    MISSING FIELD TO COLLECT:
                    {missing_field}

                    Generate an MCQ to collect this missing information."""
    logger.info(f"user prompt mcq: {user_prompt}")

    return system_prompt, user_prompt


def get_answer_generator_prompt(
    intake_data: dict, 
    chat_history: list, 
    user_question: str, 
    mcq_response: str = None
):
    system_prompt = CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT
    intake_text = json.dumps(intake_data, indent=2)
    
    # History disabled for now to reduce token usage
    # history_text = _format_history(chat_history)

    mcq_text = ""
    if mcq_response:
        mcq_text = f"\n\nUSER'S MCQ RESPONSE:\n{mcq_response}"
    
    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}
                    {mcq_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    Provide your answer and suggested follow-up questions."""
    logger.info(f"user prompt answer: {user_prompt}")

    return system_prompt, user_prompt