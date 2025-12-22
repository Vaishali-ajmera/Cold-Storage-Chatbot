TYPE_BUILD = 'build'
TYPE_EXISTING = 'existing'

USER_CHOICES = [
    (TYPE_BUILD, 'I want to build a cold storage'),
    (TYPE_EXISTING, 'I already have a cold storage'),
]

SUGGESTION_SYSTEM_PROMPT = '''
You are the Potato Cold Storage Advisor AI, an expert in post-harvest technology and cold chain logistics. Your goal is to provide 3 highly relevant, professional follow-up questions to help a user optimize their potato storage strategy.

RULES:
1. CONTEXT AWARENESS: Distinguish between users building a "NEW" facility and those managing an "EXISTING" one.
2. INDUSTRY SPECIFICITY: Use technical concepts like CIPC treatment, sprout suppression, CO2 levels, humidity control (85-95%), and Sugar-Free processing requirements where applicable.
3. OUTPUT FORMAT: You must return ONLY a JSON object with the key "suggested_questions".
4. TONE: Professional, helpful, and technical yet accessible to farmers/investors.

'''

SUGGESTION_USER_PROMPT = '''
Analyze the following User Preference Data and generate 3 smart follow-up questions.

USER DATA:
{{USER_JSON_DATA}}

GUIDELINES FOR QUESTIONS:
- If NEW: Focus on ROI, technical specifications (Chamber sizing, Insulation), or local market linkages.
- If EXISTING: Focus on solving their specific "primary_problem" (e.g., Sprouting), energy efficiency, or quality maintenance for their specific variety (e.g., Kufri Jyoti).
- Ensure questions are short (max 15 words) and encourage the user to provide more technical detail.

RESPONSE FORMAT:
{
  "suggested_questions": ["Question 1", "Question 2", "Question 3"]
}

'''

# Suggested questions mapping for frontend or API responses
SUGGESTED_QUESTIONS_DATA ={
    TYPE_BUILD: {
        "label": "I want to build a cold storage",
        "questions": [
            "Estimated cost for 5000 MT plant?",
            "Land and location requirements?",
            "How to get NHB/NABARD subsidies?",
            "Single vs. Multi-chamber design?",
            "Ammonia vs. Freon systems?",
            "Civil and flooring requirements?",
            "Average construction timeline?",
            "Required licenses and clearances?",
            "PEB vs. RCC construction?",
            "Expected ROI timeline?",
            "Electricity load calculation?",
            "Benefits of PUF panels?",
            "Need for sorting/grading sheds?",
            "Fire safety and insurance norms?",
            "How to find expert consultants?"
        ]
    },
    TYPE_EXISTING: {
        "label": "I already have a cold storage",
        "questions": [
           "How to reduce electricity bills?",
            "Ideal Temp/RH for seed potatoes?",
            "CO2 flushing frequency?",
            "How to detect Ammonia leaks?",
            "Setup digital warehouse records?",
            "CIPC application process?",
            "Improving chamber airflow?",
            "Pre-season maintenance checklist?",
            "Preventing sugar accumulation?",
            "Solar power integration?",
            "Best bag stacking patterns?",
            "Calibrating Temp/RH sensors?",
            "Handling 'Late Blight' in storage?",
            "Benefits of VFD fan upgrades?",
            "Reducing potato weight loss?"
        ]
    }
}


SYSTEM_PROMPT = """
Role: You are a Potato Cold Storage Advisory Expert.
Instructions:
1. Context Check: If the input is NOT related to potato cold storage, respond strictly with: "Out of context."
2. MCQ Mode: If the query is broad, ask ONE clarifying question with 4 MCQ options (A, B, C, D).
3. Answer Mode: If clear, give a concise answer (max 4 sentences) + 3 suggested questions.
"""

