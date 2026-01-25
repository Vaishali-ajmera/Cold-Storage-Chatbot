PURPOSE_CHOICES = [
    ("forgot_password", "Forgot Password"),
]

# Preferred Language choices
LANGUAGE_EN = "en"  # English
LANGUAGE_HI = "hi"  # Hindi
LANGUAGE_MR = "mr"  # Marathi
LANGUAGE_GU = "gu"  # Gujarati
LANGUAGE_BN = "bn"  # Bengali
LANGUAGE_PA = "pa"  # Punjabi

LANGUAGE_CHOICES = [
    (LANGUAGE_EN, "English"),
    (LANGUAGE_HI, "Hindi (हिन्दी)"),
    (LANGUAGE_MR, "Marathi (मराठी)"),
    (LANGUAGE_GU, "Gujarati (ગુજરાતી)"),
    (LANGUAGE_BN, "Bengali (বাংলা)"),
    (LANGUAGE_PA, "Punjabi (ਪੰਜਾਬੀ)")
]

DEFAULT_LANGUAGE = LANGUAGE_EN

LANGUAGE_MAP = {
    LANGUAGE_EN: "English",
    LANGUAGE_HI: "Hindi",
    LANGUAGE_MR: "Marathi",
    LANGUAGE_GU: "Gujarati",
    LANGUAGE_BN: "Bengali",
    LANGUAGE_PA: "Punjabi",
}
