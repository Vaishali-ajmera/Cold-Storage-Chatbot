def get_classifier_prompt(intake_data, chat_history, user_question):
    """
    PROMPT 1: Classify user question into one of 3 paths
    
    Args:
        intake_data: Dict with 'user_choice' and 'intake_data'
        chat_history: List of message dicts
        user_question: String
    
    Returns: JSON with classification decision
    """

    system_prompt = """You are a strict query classifier for a cold storage advisory system.

TASK:
Analyze the user's question and classify it into ONE of these categories:

1. ANSWER_DIRECTLY
   - Question is about cold storage/crops
   - We have enough context from intake data to answer
   - Examples: "What temperature for potatoes?", "How to prevent spoilage?"

2. NEEDS_FOLLOW_UP
   - Question is relevant to cold storage
   - BUT we're missing critical information to answer properly
   - Examples: "What's the electricity cost?" (missing: duration), "Investment needed?" (missing: scale)

3. OUT_OF_CONTEXT
   - Question is completely unrelated to cold storage, crops, or post-harvest operations
   - Examples: "What's Bitcoin price?", "Tell me a joke", "Weather tomorrow?"

RULES:
- Choose ONLY ONE category
- Do NOT answer the question
- If NEEDS_FOLLOW_UP, specify which field is missing
- Be strict about OUT_OF_CONTEXT - only cold storage topics are valid

OUTPUT FORMAT (STRICT JSON):
{
  "classification": "ANSWER_DIRECTLY" | "NEEDS_FOLLOW_UP" | "OUT_OF_CONTEXT",
  "missing_field": "field_name" or null,
  "reasoning": "brief 1-sentence explanation"
}"""

    # Format intake data
    user_choice = intake_data.get("user_choice", "unknown")
    data = intake_data.get("intake_data", {})
    
    intake_text = f"""User Type: {user_choice}
Location: {data.get('location', 'Not specified')}
State: {data.get('state', 'Not specified')}
Crop: {data.get('crop_type', 'Not specified')}"""
    
    if user_choice == "owner":
        intake_text += f"""
Capacity: {data.get('capacity_mt', 'Not specified')} MT
Potato Variety: {data.get('potato_variety', 'Not specified')}
Storage Goal: {data.get('storage_goal', 'Not specified')}
Current Problems: {data.get('current_problems', 'None mentioned')}"""
    else:  # builder
        intake_text += f"""
Planned Capacity: {data.get('planned_capacity_mt', 'Not specified')} MT
Budget Range: {data.get('budget_range', 'Not specified')}
Business Model: {data.get('business_model', 'Not specified')}
Timeline: {data.get('timeline', 'Not specified')}"""

    # Format chat history
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
    """
    PROMPT 2: Generate MCQ to collect missing information

    Returns: JSON with MCQ question and 4 options
    """

    system_prompt = """You are an MCQ generator for a cold storage advisory system.

TASK:
Generate ONE multiple-choice question to collect the missing information needed to answer the user's question.

RULES:
- Provide exactly 4 options (A, B, C, D)
- Options must be:
  * Short (3-6 words each)
  * Mutually exclusive
  * Practical and commonly applicable
  * Cover the typical range of values
- Question must be clear and direct
- Do NOT include information already in intake data

OUTPUT FORMAT (STRICT JSON):
{
  "question": "Clear, direct question text?",
  "options": [
    {"key": "A", "value": "First option"},
    {"key": "B", "value": "Second option"},
    {"key": "C", "value": "Third option"},
    {"key": "D", "value": "Fourth option"}
  ]
}"""

    # Format intake data
    user_choice = intake_data.get("user_choice", "unknown")
    data = intake_data.get("intake_data", {})
    
    intake_text = f"""User Type: {user_choice}
Location: {data.get('location', 'Not specified')}
State: {data.get('state', 'Not specified')}
Crop: {data.get('crop_type', 'Not specified')}"""

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
    """
    PROMPT 3: Generate final answer with suggestions

    Returns: JSON with answer text and 3 suggested questions
    """

    system_prompt = """You are a senior cold storage technical advisor with 20+ years of experience.

TASK:
Answer the user's question using the provided context. Also generate 3 relevant follow-up questions.

KNOWLEDGE SOURCES (in priority order):
1. Internal knowledge base and domain expertise (PRIMARY)
2. User's intake data and conversation history
3. Your general training knowledge
4. If needed: current market data (but clearly mark as external)

ANSWER GUIDELINES:
- Be specific and practical
- Use exact numbers/ranges where applicable
- Reference user's context (location, crop, capacity) naturally
- Keep answers concise (3-5 sentences for simple questions, more for complex)
- If suggesting investments/changes, give approximate costs in INR
- Mention climate considerations for their location
- No fluff or generic advice

SUGGESTED QUESTIONS RULES:
- Provide exactly 3 follow-up questions
- Each must be 5-8 words
- Must be directly related to the answer you gave
- Must help user take next practical steps
- Use question marks

OUTPUT FORMAT (STRICT JSON):
{
  "answer": "Your detailed answer here",
  "suggested_questions": [
    "First relevant question?",
    "Second relevant question?",
    "Third relevant question?"
  ]
}"""

    # Format intake data
    user_choice = intake_data.get("user_choice", "unknown")
    data = intake_data.get("intake_data", {})
    
    intake_text = f"""User Type: {user_choice}
Location: {data.get('location', 'Not specified')}
State: {data.get('state', 'Not specified')}
Crop: {data.get('crop_type', 'Not specified')}"""
    
    if user_choice == "owner":
        intake_text += f"""
Capacity: {data.get('capacity_mt', 'Not specified')} MT
Potato Variety: {data.get('potato_variety', 'Not specified')}
Storage Goal: {data.get('storage_goal', 'Not specified')}
Current Problems: {data.get('current_problems', 'None mentioned')}"""
    else:  # builder
        intake_text += f"""
Planned Capacity: {data.get('planned_capacity_mt', 'Not specified')} MT
Budget Range: {data.get('budget_range', 'Not specified')}
Business Model: {data.get('business_model', 'Not specified')}
Timeline: {data.get('timeline', 'Not specified')}"""

    # Format chat history
    history_text = ""
    if chat_history:
        history_text = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in chat_history:
            history_text += f"{msg['sender'].upper()}: {msg['message']}\n"

    # Format MCQ response if present
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


def get_rejection_message():
    """
    Standard rejection message for out-of-context questions
    No LLM needed - just return this
    """
    return {
        "message": (
            "I specialize in cold storage advisory for crops. "
            "I can help with topics like:\n"
            "• Storage temperature and humidity control\n"
            "• Facility design and equipment\n"
            "• Spoilage prevention and quality management\n"
            "• Operational costs and ROI\n"
            "• Post-harvest handling\n\n"
            "Please ask a question related to cold storage operations."
        ),
        "suggested_questions": [
            "What's the ideal storage temperature?",
            "How to prevent spoilage in storage?",
            "What are typical operational costs?",
        ],
    }
