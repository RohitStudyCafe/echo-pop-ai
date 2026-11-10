from app.memory.session_context import (
    get_history_from_session,
    append_to_session_history,
    clear_session_history,
    get_preferred_provider,
    set_preferred_provider,
    SESSION_HISTORY_KEY
)

def test_session_history_empty():
    history = get_history_from_session({})
    assert history == []

def test_append_and_retrieve_history():
    attrs = {}
    attrs = append_to_session_history(attrs, role="user", content="Hello")
    attrs = append_to_session_history(attrs, role="assistant", content="Hi there!")
    
    history = get_history_from_session(attrs)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "Hello"
    assert history[1].role == "assistant"
    assert history[1].content == "Hi there!"

def test_sliding_window_limit():
    attrs = {}
    for i in range(12):
        attrs = append_to_session_history(attrs, role="user", content=f"msg {i}", max_messages=4)
    
    history = get_history_from_session(attrs)
    assert len(history) == 4
    assert history[-1].content == "msg 11"
    assert history[0].content == "msg 8"

def test_clear_session_history():
    attrs = {"preferred_provider": "gemini"}
    attrs = append_to_session_history(attrs, role="user", content="Hi")
    attrs = clear_session_history(attrs)
    
    assert get_history_from_session(attrs) == []
    # Verify other session attributes were preserved
    assert attrs["preferred_provider"] == "gemini"

def test_preferred_provider():
    attrs = {}
    assert get_preferred_provider(attrs) is None
    attrs = set_preferred_provider(attrs, "gemini")
    assert get_preferred_provider(attrs) == "gemini"

