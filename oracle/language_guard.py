import re

FORBIDDEN_TERMS = [
    "apuesta", "apostar", "pick", "ganador", "recomendado", "recomendación",
    "seguro", "lock", "stake", "cuota", "odds", "parlay", "combinada"
]

ALLOWED_REPLACEMENTS = {
    "odds": "precio de referencia",
    "cuota": "precio de referencia",
    "pick": "opción",
    "ganador": "resultado",
    "apuesta": "decisión"
}

def language_guard(text: str) -> str:
    """
    Deterministic guard: remove/replace forbidden terms; 
    if cannot sanitize, hard-fail.
    """
    original_text = text
    
    # 1. Try to replace terms that have direct mappings
    for term, replacement in ALLOWED_REPLACEMENTS.items():
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(replacement, text)
        
    # 2. For other forbidden terms, try to remove them if they still exist
    for term in FORBIDDEN_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(text):
            # Check if it was already replaced (case where term is key in ALLOWED_REPLACEMENTS)
            if term not in ALLOWED_REPLACEMENTS:
                text = pattern.sub("", text)

    # 3. Final verification - Hard fail if any forbidden term remains
    lower_text = text.lower()
    for term in FORBIDDEN_TERMS:
        if term in lower_text:
            raise ValueError(f"Language guard failure: Forbidden term '{term}' detected and could not be sanitized in text: {text[:100]}...")

    return text

if __name__ == "__main__":
    # Test cases
    test_text = "Nuestra recomendación es apostar por el ganador con mejores odds."
    print(f"Original: {test_text}")
    print(f"Sanitized: {language_guard(test_text)}")
