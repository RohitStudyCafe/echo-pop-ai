import re

def clean_text_for_alexa(text: str) -> str:
    # 1. Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 2. Remove code blocks ```...```
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 3. Remove inline code `...`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 4. Remove bold/italic **text**, *text*, __text__, _text_
    text = re.sub(r'(\*\*|\*|__|_)', '', text)
    
    # 5. Remove emojis
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # 6. Replace bullet points/lists with commas
    text = re.sub(r'^\s*[\*\-\+]\s+', ', ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', ', ', text, flags=re.MULTILINE)
    
    # 7. Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 8. Limit length to 1000 characters for snappy TTS
    return text[:1000]

