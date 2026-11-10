from app.utils.text_cleaner import clean_text_for_alexa

def test_clean_markdown_links():
    assert clean_text_for_alexa("Check [this link](http://example.com) for details.") == "Check this link for details."

def test_clean_code_blocks():
    text = "Here is the code:\n```python\nprint('hello')\n```\nDone."
    assert clean_text_for_alexa(text) == "Here is the code: Done."

def test_clean_formatting():
    assert clean_text_for_alexa("**bold text** and *italic text* and `inline code`") == "bold text and italic text and inline code"

def test_clean_lists():
    text = """
    Here are steps:
    * step one
    * step two
    1. step three
    """
    cleaned = clean_text_for_alexa(text)
    assert "step one" in cleaned
    assert "step two" in cleaned
    assert "step three" in cleaned
    assert "," in cleaned

def test_clean_emojis():
    assert clean_text_for_alexa("Hello world! 🚀🌟") == "Hello world!"

def test_truncation():
    long_text = "word " * 300
    cleaned = clean_text_for_alexa(long_text)
    assert len(cleaned) <= 1000
