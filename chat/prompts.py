import json

from chat.constants import (
    CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT,
    CHAT_CLASSIFIER_SYSTEM_PROMPT,
    CHAT_MCQ_GENERATOR_SYSTEM_PROMPT,
    CHAT_OUT_OF_CONTEXT_MESSAGE,
)


def get_classifier_prompt(intake_data, chat_history, user_question):
    system_prompt = CHAT_CLASSIFIER_SYSTEM_PROMPT

    intake_text = json.dumps(intake_data, indent=2)

    history_text = ""
    if chat_history:
        history_text = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in chat_history:
            history_text += f"{msg['sender'].upper()}: {msg['message']}\n"

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}
                    {history_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    Classify this question now."""

    return system_prompt, user_prompt


def get_mcq_generator_prompt(intake_data, user_question, missing_field):
    system_prompt = CHAT_MCQ_GENERATOR_SYSTEM_PROMPT

    intake_text = json.dumps(intake_data, indent=2)

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}

                    USER'S ORIGINAL QUESTION:
                    "{user_question}"

                    MISSING FIELD TO COLLECT:
                    {missing_field}

                    Generate an MCQ to collect this missing information."""

    return system_prompt, user_prompt


def get_answer_generator_prompt(
    intake_data, chat_history, user_question, mcq_response=None
):
    system_prompt = CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT

    intake_text = json.dumps(intake_data, indent=2)

    history_text = ""
    if chat_history:
        history_text = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in chat_history:
            history_text += f"{msg['sender'].upper()}: {msg['message']}\n"

    mcq_text = ""
    if mcq_response:
        mcq_text = f"\n\nUSER'S MCQ RESPONSE:\n{mcq_response}"

    user_prompt = f"""USER INTAKE DATA:
                    {intake_text}
                    {history_text}
                    {mcq_text}

                    CURRENT USER QUESTION:
                    "{user_question}"

                    Provide your answer and suggested follow-up questions."""

    return system_prompt, user_prompt
