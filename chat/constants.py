# Message types
MESSAGE_TYPE_USER_QUESTION = "user_question"
MESSAGE_TYPE_BOT_ANSWER = "bot_answer"
MESSAGE_TYPE_BOT_MCQ = "bot_mcq_question"
MESSAGE_TYPE_USER_MCQ = "user_mcq_response"
MESSAGE_TYPE_BOT_REJECTION = "bot_rejection"
MESSAGE_TYPE_BOT_LIMIT = "bot_limit_reached"

MESSAGE_TYPE_CHOICES = [
    (MESSAGE_TYPE_USER_QUESTION, "User Question"),
    (MESSAGE_TYPE_BOT_ANSWER, "Bot Answer"),
    (MESSAGE_TYPE_BOT_MCQ, "Bot MCQ Question"),
    (MESSAGE_TYPE_USER_MCQ, "User MCQ Response"),
    (MESSAGE_TYPE_BOT_REJECTION, "Bot Rejection"),
    (MESSAGE_TYPE_BOT_LIMIT, "Bot Limit Reached"),
]

# Sender types
SENDER_USER = "user"
SENDER_BOT = "bot"

SENDER_CHOICES = [
    (SENDER_USER, "User"),
    (SENDER_BOT, "Bot"),
]

# Session status
SESSION_ACTIVE = "active"
SESSION_COMPLETED = "completed"
SESSION_ABANDONED = "abandoned"
SESSION_LIMIT_REACHED = "limit_reached"

SESSION_STATUS_CHOICES = [
    (SESSION_ACTIVE, "Active"),
    (SESSION_COMPLETED, "Completed"),
    (SESSION_ABANDONED, "Abandoned"),
    (SESSION_LIMIT_REACHED, "Limit Reached"),
]

# Configuration
DEFAULT_MAX_QUESTIONS = 4
DEFAULT_SESSION_TIMEOUT_HOURS = 24


# =============================================================================
# CHAT API SYSTEM PROMPTS (Used by chat/views.py)
# =============================================================================

CHAT_CLASSIFIER_SYSTEM_PROMPT = """You are a strict query classifier for a cold storage advisory system.

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


CHAT_MCQ_GENERATOR_SYSTEM_PROMPT = """You are an MCQ generator for a cold storage advisory system.

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


CHAT_ANSWER_GENERATOR_SYSTEM_PROMPT = """You are a senior cold storage technical advisor with 20+ years of experience.

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


CHAT_OUT_OF_CONTEXT_MESSAGE = {
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
