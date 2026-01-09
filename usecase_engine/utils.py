import json


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
