import re

def clean_text_for_alexa(text: str) -> str:
    if not text:
        return ""

    # Replace smart typography and programming symbols with clear spoken words
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": ", ",   # em-dash
        "\u2013": ", ",   # en-dash
        "\u2026": "...",  # ellipsis
        "&": " and ",
        "+": " plus ",
        "#": " sharp ",   # e.g., C# -> C sharp
        "->": " leads to ",
        "=>": " results in ",
        "!=": " not equal to ",
        "==": " equals ",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)

    # 1. Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 2. Remove multiline code blocks (replace with clean space so words aren't glued together)
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    
    # 3. Remove inline backticks `code` -> code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 4. Remove bold/italic markdown **text**, *text*, __text__, _text_
    text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
    
    # 5. Convert bullet points and numbered lists to natural spoken flow
    text = re.sub(r'^\s*[\*\-\+]\s+', ', ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', ', ', text, flags=re.MULTILINE)
    
    # 6. Remove unpronounceable emojis while keeping standard printable characters
    text = re.sub(r'[^\x20-\x7E]', '', text)
    
    # 7. Clean up whitespace and stuttered commas
    text = re.sub(r',\s*,+', ',', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 8. Clean sentence-aware truncation (never cut off mid-word or mid-sentence)
    if len(text) > 1000:
        truncated = text[:1000]
        last_punct = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
        if last_punct > 400:
            text = truncated[:last_punct + 1]
        else:
            text = truncated.rsplit(' ', 1)[0] + "."

    return text
