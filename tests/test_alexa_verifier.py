import datetime
from app.alexa.verifier import is_valid_cert_url, is_timestamp_fresh

def test_valid_cert_url():
    valid = "https://s3.amazonaws.com/echo.api/echo-api-cert-8.pem"
    assert is_valid_cert_url(valid) is True

    valid_port = "https://s3.amazonaws.com:443/echo.api/echo-api-cert-8.pem"
    assert is_valid_cert_url(valid_port) is True

    # Invalid scheme
    assert is_valid_cert_url("http://s3.amazonaws.com/echo.api/cert.pem") is False
    # Invalid host
    assert is_valid_cert_url("https://evil.com/echo.api/cert.pem") is False
    # Invalid path
    assert is_valid_cert_url("https://s3.amazonaws.com/other/cert.pem") is False
    # Invalid port
    assert is_valid_cert_url("https://s3.amazonaws.com:8080/echo.api/cert.pem") is False

def test_timestamp_freshness():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert is_timestamp_fresh(now_iso, max_drift_seconds=150) is True

    # Test old timestamp (300 seconds ago)
    old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=300)).isoformat()
    assert is_timestamp_fresh(old, max_drift_seconds=150) is False

    # Invalid format
    assert is_timestamp_fresh("invalid-timestamp") is False

