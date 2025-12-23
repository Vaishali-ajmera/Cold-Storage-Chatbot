TYPE_BUILD = "build"
TYPE_EXISTING = "existing"

USER_CHOICES = [
    (TYPE_BUILD, "I want to build a cold storage"),
    (TYPE_EXISTING, "I already have a cold storage"),
]

SUGGESTED_QUESTIONS_SYSTEM_PROMPT = """
ROLE:
You are a senior cold storage consultant specializing in agricultural cold chains.

GOAL:
Generate EXACTLY 3 ultra-short, UI-friendly suggested questions for a chatbot.

STYLE RULES (STRICT):
- Each item must be 4–6 words maximum.
- Use short, action-oriented phrases.
- No full sentences.
- No punctuation.
- No numbering.
- No explanations.

INTENT RULES:
- EXISTING storage → optimization, cost reduction, efficiency, storage strategy, market timing.
- BUILD storage → feasibility, design, capacity planning, technology choice, ROI.

DOMAIN RULES (CONDITIONAL — NOT HARD-CODED):
- If the crop variety is processing-grade → focus on sugar control, temperature strategy, and quality retention.
- If the crop variety is table-grade → focus on sprouting control, weight loss, and shelf life.
- If electricity or power cost is mentioned → focus on energy optimization (insulation, VFD, solar, refrigeration efficiency).
- If market timing or price is mentioned → focus on holding period, price trends, and release strategy.
- If location implies high production or high energy cost → consider regional power tariffs, subsidies, and market behavior.

OUTPUT FORMAT (STRICT):
Return ONLY a valid JSON array of exactly 3 strings.
Example:
[
  "Reduce electricity costs",
  "Optimal storage temperature",
  "Best market release timing"
]
"""


SUGGESTION_USER_PROMPT = """
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

"""

# Suggested questions mapping for frontend or API responses
SUGGESTED_QUESTIONS_DATA = {
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
            "How to find expert consultants?",
        ],
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
            "Reducing potato weight loss?",
        ],
    },
}


SYSTEM_PROMPT = """
Role: You are a specialized Potato Cold Storage Advisory Expert.

Core Objectives:
1. Context Validation:
   - Determine if the user's message is related to potato cultivation, cold storage technology, post-harvest management, or related agricultural logistics.
   - If the message is unrelated, respond ONLY with: "Out of context."

2. Information Gathering (MCQ Mode):
   - If the user's query is too vague to provide a technical recommendation (e.g., "how to start?"), generate ONE clarifying question followed by exactly 4 choices (labeled A, B, C, D).
   - Format: [Clarifying Question] \n A) [Choice 1] \n B) [Choice 2] \n C) [Choice 3] \n D) [Choice 4]

3. Expert Advisory (Answer Mode):
   - If the query is specific, provide a concise, high-value technical answer (maximum 4-5 sentences).
   - After the answer, provide exactly 3 suggested follow-up questions for the user to explore further.
   - Format: [Direct Answer] \n\n Suggested Questions: \n 1. [Q1] \n 2. [Q2] \n 3. [Q3]

Tone: Professional, data-driven, and focused on operational efficiency.
"""


# Dummy responses for testing (will be replaced by actual LLM later)
DUMMY_RESPONSES = {
    # Out of Context Detection
    "what is the best recipe for making potato chips": {
        "status": "out_of_context",
        "message": "Query is out of context",
        "data": {
            "answer": "I can only help with questions related to potato cold storage and advisory. Please ask questions about potato storage, cold storage operations, or related topics.",
            "type": "out_of_context",
        },
    },
    "how to cook potatoes": {
        "status": "out_of_context",
        "message": "Query is out of context",
        "data": {
            "answer": "I can only help with questions related to potato cold storage and advisory. Please ask questions about potato storage, cold storage operations, or related topics.",
            "type": "out_of_context",
        },
    },
    # ============================================
    # MCQ FLOW - STEP 1: Ask MCQ Question
    # ============================================
    "my potatoes are sprouting heavily in storage, what to do?": {
        "status": "need_more_info",
        "message": "Need more information",
        "data": {
            "question": "To give you the best advice on controlling sprouting, what is your current storage temperature?",
            "type": "mcq",
            "options": ["Below 2°C", "2-4°C", "4-6°C", "Above 6°C"],
        },
    },
    # ============================================
    # MCQ FLOW - STEP 2: User Selected "Below 2°C"
    # ============================================
    "my potatoes are sprouting heavily in storage below 2°c": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "At below 2°C, sprouting should NOT occur - but you're risking cold-induced sweetening and blackheart disease. If you're still seeing sprouts, your temperature sensors may be faulty or placement is wrong. Immediately: 1) Calibrate all temperature sensors, 2) Check if cold air is reaching all zones uniformly, 3) Verify potatoes weren't already sprouted at intake. Consider raising temperature to 2-3°C for table potatoes.",
            "type": "answer",
            "suggested_questions": [
                "How do I calibrate temperature sensors in cold storage?",
                "What is cold-induced sweetening and how to avoid it?",
                "Where should temperature sensors be placed in the storage?",
            ],
        },
    },
    # ============================================
    # MCQ FLOW - STEP 2: User Selected "2-4°C"
    # ============================================
    "my potatoes are sprouting heavily in storage 2-4°c": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "At 2-4°C, sprouting should be minimal. Your issue likely stems from: 1) High humidity (keep it 85-90%, not above 95%), 2) Light exposure (ensure complete darkness), or 3) Ethylene gas from other produce. Also check if you're storing seed potatoes - they naturally sprout faster than table varieties. Consider applying sprout inhibitors like CIPC (Chlorpropham) if organic methods fail.",
            "type": "answer",
            "suggested_questions": [
                "What sprout inhibitors are approved for use in India?",
                "How do I control humidity levels in my cold storage?",
                "Can I store different potato varieties together?",
            ],
        },
    },
    # ============================================
    # MCQ FLOW - STEP 2: User Selected "4-6°C"
    # ============================================
    "my potatoes are sprouting heavily in storage 4-6°c": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "4-6°C is TOO WARM for potato storage - this is your main problem. Sprouting accelerates rapidly above 4°C. Immediately lower temperature to 2-4°C for table potatoes or 1-2°C for seed potatoes. Each 1°C increase above 4°C doubles sprouting rate. Also ensure: 1) Complete darkness, 2) 85-90% humidity, 3) Proper ventilation (30-40 CFM/ton). This temperature is only acceptable for very short-term storage (2-3 weeks).",
            "type": "answer",
            "suggested_questions": [
                "How quickly can I safely lower the storage temperature?",
                "Will lowering temperature stop existing sprouts from growing?",
                "What is the maximum acceptable temperature for 6-month storage?",
            ],
        },
    },
    # ============================================
    # MCQ FLOW - STEP 2: User Selected "Above 6°C"
    # ============================================
    "my potatoes are sprouting heavily in storage above 6°c": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "Above 6°C is CRITICALLY HIGH for potato storage - massive sprouting is expected and inevitable at this temperature. You're essentially storing at room temperature. URGENT ACTION: 1) Lower temperature to 2-4°C immediately (do it gradually - 1°C per day to avoid condensation), 2) Sort and remove heavily sprouted potatoes, 3) Check if your cooling system is malfunctioning. At this temperature, you'll also face high weight loss (10-15%) and quality degradation within weeks.",
            "type": "answer",
            "suggested_questions": [
                "How do I troubleshoot my cooling system?",
                "Can I still sell potatoes that have sprouted?",
                "What is the safe rate to lower storage temperature?",
            ],
        },
    },
    # ============================================
    # ANOTHER MCQ FLOW - Construction Cost
    # ============================================
    "what is the cost per mt to build a cold storage in punjab": {
        "status": "need_more_info",
        "message": "Need more information",
        "data": {
            "question": "Construction costs vary significantly by capacity. What is your planned storage capacity?",
            "type": "mcq",
            "options": [
                "Less than 1000 MT",
                "1000-5000 MT",
                "5000-10000 MT",
                "Above 10000 MT",
            ],
        },
    },
    # MCQ Answer - Less than 1000 MT
    "what is the cost per mt to build a cold storage in punjab less than 1000 mt": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For <1000 MT capacity in Punjab, expect ₹8,000-₹12,000 per MT construction cost. Total project cost including land, equipment, licensing: ₹80 lakhs - ₹1.2 crores. Higher per-MT cost due to economies of scale. Government subsidies available: NABARD provides 35% subsidy (up to ₹3.5 crores). ROI period: 7-10 years. Key costs: PUF insulation (₹450/sqft), compressor (₹15-20 lakhs), electrical (₹8-12 lakhs).",
            "type": "answer",
            "suggested_questions": [
                "What government subsidies are available for cold storage construction?",
                "What is the typical ROI period for a small cold storage?",
                "Should I rent space initially instead of building?",
            ],
        },
    },
    # MCQ Answer - 1000-5000 MT
    "what is the cost per mt to build a cold storage in punjab 1000-5000 mt": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For 1000-5000 MT capacity in Punjab, expect ₹5,500-₹8,000 per MT construction cost. Total project: ₹2-4 crores. This is the optimal range for small/medium farmers. Government subsidies: NABARD 35% (up to ₹3.5 crores) + state subsidies 15-20%. ROI: 5-7 years. Operating cost: ₹250-350 per MT per month. Consider modular design for phased expansion.",
            "type": "answer",
            "suggested_questions": [
                "What is modular cold storage design?",
                "Can I get a bank loan for cold storage construction?",
                "What are typical rental rates I can charge farmers?",
            ],
        },
    },
    # MCQ Answer - 5000-10000 MT
    "what is the cost per mt to build a cold storage in punjab 5000-10000 mt": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For 5000-10000 MT capacity in Punjab, expect ₹4,500-₹6,500 per MT construction cost. Total: ₹3-6.5 crores. Best economies of scale. Subsidies: NABARD 35% + Punjab Mandi Board incentives. ROI: 4-6 years. Consider multi-chamber design for different crops/clients. Operating cost: ₹180-250 per MT per month. This size attracts FPOs and large traders as anchor clients.",
            "type": "answer",
            "suggested_questions": [
                "What is multi-chamber cold storage design?",
                "How do I find anchor clients before construction?",
                "Should I integrate potato processing unit with storage?",
            ],
        },
    },
    # MCQ Answer - Above 10000 MT
    "what is the cost per mt to build a cold storage in punjab above 10000 mt": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For >10000 MT capacity in Punjab, expect ₹3,800-₹5,500 per MT construction cost. Total: ₹5+ crores. Maximum economies of scale but requires significant land (5-10 acres) and high working capital. Consider automated systems, solar integration (saves 30% energy), and CA storage for premium clients. ROI: 4-5 years. Target corporate buyers, processing units, and export markets.",
            "type": "answer",
            "suggested_questions": [
                "What is CA (Controlled Atmosphere) storage?",
                "Is solar power viable for large cold storage?",
                "What automation systems should I include?",
            ],
        },
    },
    # Direct Answer with Suggested Questions
    "what is the ideal temperature for storing kufri jyoti potatoes for table use": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For Kufri Jyoti table potatoes, maintain 2-4°C with 85-90% relative humidity. This variety stores well for 4-5 months at this temperature. Avoid going below 2°C as it causes cold-induced sweetening (high reducing sugars), making potatoes unsuitable for cooking. Keep ventilation at 30-40 CFM per ton and ensure complete darkness to prevent greening.",
            "type": "answer",
            "suggested_questions": [
                "How often should I check the stored potatoes for quality?",
                "What are signs of cold-induced sweetening in potatoes?",
                "How can I prevent weight loss during long-term storage?",
            ],
        },
    },
    "my electricity bills are very high how can i reduce them": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "To reduce cold storage electricity costs: 1) Install VFD (Variable Frequency Drive) compressors - saves 20-30% energy, 2) Improve insulation (PUF panels 100-150mm thick), 3) Use LED lights instead of traditional bulbs, 4) Maintain optimal temperature (each 1°C lower increases cost by 3-5%), 5) Schedule defrosting during off-peak hours. ROI on VFD is typically 2-3 years. For a 2000 MT facility, you can save ₹3-5 lakhs annually.",
            "type": "answer",
            "suggested_questions": [
                "What is VFD and how does it work?",
                "Should I switch to solar power for my cold storage?",
                "How much insulation thickness is optimal for my capacity?",
            ],
        },
    },
    "which potato variety is best for long term storage in uttar pradesh": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "For UP conditions, Kufri Pukhraj is best for long-term storage (6-8 months) due to high dry matter and dormancy. Kufri Jyoti is also excellent (4-6 months) and has good market demand. Avoid Kufri Chandramukhi for long storage as it has shorter dormancy. For processing industry, Kufri Chipsona varieties store well. Store at 2-4°C with 85-90% RH for optimal results.",
            "type": "answer",
            "suggested_questions": [
                "What is the difference between Kufri Pukhraj and Kufri Jyoti storage requirements?",
                "Can I mix different varieties in the same cold storage chamber?",
                "How do I identify the right harvesting time for long storage?",
            ],
        },
    },
    "i am seeing black spots inside my stored potatoes": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "Black spots inside potatoes indicate blackheart disease, caused by oxygen deficiency. This happens when: 1) Storage temperature is too low (<0°C), 2) Poor ventilation (needs 30-40 CFM/ton), 3) CO2 buildup (should be <1%). Immediately improve air circulation, check temperature sensors, and remove affected potatoes. This is NOT infectious - it's a physiological disorder. Prevention: maintain proper ventilation and never store below 1°C.",
            "type": "answer",
            "suggested_questions": [
                "What ventilation system should I install for my capacity?",
                "How do I test CO2 levels in my cold storage?",
                "Is blackheart disease the same as black scurf?",
            ],
        },
    },
    "i am losing 8 to 10 percent weight during 6 months storage is this normal": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "8-10% weight loss is higher than acceptable. Normal weight loss should be 4-6% over 6 months. Your high loss indicates: 1) Low humidity (should be 85-90%, likely yours is <80%), 2) Poor sealing/air leaks, 3) Over-ventilation, or 4) Temperature fluctuations. Install humidifiers, check door seals, and maintain stable temperature. Each 10% RH drop increases weight loss by 2-3%. Fixing this can save ₹50,000-₹1 lakh per 1000 MT.",
            "type": "answer",
            "suggested_questions": [
                "What type of humidifier should I use in cold storage?",
                "How do I detect air leaks in my facility?",
                "What is the economic impact of weight loss per MT?",
            ],
        },
    },
    "i want to also store onions in my potato cold storage": {
        "status": "answered",
        "message": "Response generated successfully",
        "data": {
            "answer": "Do NOT store onions and potatoes together in the same chamber. Potatoes need 2-4°C and 85-90% humidity, while onions need 0-1°C and 65-70% humidity. More critically, onions absorb potato odor and potatoes absorb moisture from onions, both degrading quality. If you must use the same facility, create separate insulated chambers with independent controls.",
            "type": "answer",
            "suggested_questions": [
                "Can I store different potato varieties together?",
                "What other crops can be stored with potatoes?",
                "How do I create separate zones in my existing cold storage?",
            ],
        },
    },
}


# MCQ Context Mapping - Links user's MCQ answer back to original question
MCQ_CONTEXT_MAP = {
    # When last_question contains this key, and user sends this answer
    "sprouting": {
        "below 2°c": "my potatoes are sprouting heavily in storage below 2°c",
        "2-4°c": "my potatoes are sprouting heavily in storage 2-4°c",
        "4-6°c": "my potatoes are sprouting heavily in storage 4-6°c",
        "above 6°c": "my potatoes are sprouting heavily in storage above 6°c",
    },
    "cost per mt": {
        "less than 1000 mt": "what is the cost per mt to build a cold storage in punjab less than 1000 mt",
        "1000-5000 mt": "what is the cost per mt to build a cold storage in punjab 1000-5000 mt",
        "5000-10000 mt": "what is the cost per mt to build a cold storage in punjab 5000-10000 mt",
        "above 10000 mt": "what is the cost per mt to build a cold storage in punjab above 10000 mt",
    },
}
