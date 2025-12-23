import json

from usecase_engine.constants import DUMMY_RESPONSES, MCQ_CONTEXT_MAP


def get_dummy_response(question, last_question=None):
    """
    Get dummy response based on question.
    If last_question exists, check if this is an MCQ answer.
    """
    normalized_question = question.lower().strip()

    # Check if this is an MCQ answer (user just sent "2-4°C")
    if last_question:
        last_q_normalized = last_question.lower()

        # Try to find which MCQ context this belongs to
        for context_key, answers in MCQ_CONTEXT_MAP.items():
            if context_key in last_q_normalized:
                # Check if user's answer matches any option
                for option_key, full_question in answers.items():
                    if option_key in normalized_question:
                        # Found the matching follow-up question
                        return DUMMY_RESPONSES.get(full_question)

    # Direct match
    if normalized_question in DUMMY_RESPONSES:
        return DUMMY_RESPONSES[normalized_question]

    # Partial match for flexibility
    for key, value in DUMMY_RESPONSES.items():
        if key in normalized_question or normalized_question in key:
            return value

    return None


def get_suggested_questions_user_prompt(user_choice_key, intake_data):
    intent_map = {
        "build": "User Intent: Build a NEW cold storage facility for potato crop.",
        "existing": "User Intent: Optimize an EXISTING cold storage facility for potato crop.",
    }

    intent_desc = intent_map.get(user_choice_key, "User Intent: General inquiry.")

    return f"""
{intent_desc}

USER INTAKE DATA:
{json.dumps(intake_data, indent=2)}

TASK:
Generate 3 high-impact questions the user would logically ask next.
"""
