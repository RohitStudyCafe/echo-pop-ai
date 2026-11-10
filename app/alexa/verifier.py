import base64
import datetime
import logging
from urllib.parse import urlparse
import httpx
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger("alexa_ai.verifier")

# Cache downloaded certificates in-memory by URL to avoid downloading on every request
_CERT_CACHE: dict[str, x509.Certificate] = {}

def is_valid_cert_url(url_str: str) -> bool:
    """Validates the Amazon Echo certificate chain URL per ASK requirements."""
    try:
        parsed = urlparse(url_str)
        if parsed.scheme.lower() != "https":
            return False
        if parsed.hostname.lower() != "s3.amazonaws.com":
            return False
        if not parsed.path.startswith("/echo.api/"):
            return False
        if parsed.port not in (None, 443):
            return False
        return True
    except Exception:
        return False

def is_timestamp_fresh(timestamp_str: str, max_drift_seconds: int = 150) -> bool:
    """Verifies that the request timestamp is within +/- max_drift_seconds of UTC now."""
    try:
        # Standard format: 2019-05-13T12:34:56Z
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        req_time = datetime.datetime.fromisoformat(timestamp_str)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        drift = abs((now_utc - req_time).total_seconds())
        return drift <= max_drift_seconds
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return False

async def get_certificate(cert_url: str) -> x509.Certificate:
    """Retrieves and parses the Amazon Echo certificate, with caching."""
    if cert_url in _CERT_CACHE:
        return _CERT_CACHE[cert_url]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(cert_url)
        resp.raise_for_status()
        cert_data = resp.content
    
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    
    # Check certificate validity dates
    now = datetime.datetime.now(datetime.timezone.utc)
    if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
        raise ValueError("Certificate is expired or not yet valid.")
    
    # Subject Alternative Name must include echo-api.amazon.com
    try:
        san = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        dns_names = san.value.get_values_for_type(x509.DNSName)
        if "echo-api.amazon.com" not in dns_names:
            raise ValueError("Certificate does not contain echo-api.amazon.com in SAN")
    except x509.ExtensionNotFound:
        raise ValueError("Certificate lacks SAN extension")

    _CERT_CACHE[cert_url] = cert
    return cert

async def verify_alexa_request(request: Request, raw_body: bytes, request_timestamp: str):
    """
    Middleware/dependency to verify request authenticity.
    If settings.VERIFY_ALEXA_SIGNATURE is False, verification is skipped.
    """
    if not settings.VERIFY_ALEXA_SIGNATURE:
        return  # Verification bypassed for local testing / development

    # Verify timestamp freshness
    if not is_timestamp_fresh(request_timestamp):
        logger.warning("Rejected Alexa request: timestamp is expired or too far in the future.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request timestamp is outside the allowed window."
        )

    cert_url = request.headers.get("SignatureCertChainUrl")
    signature_b64 = request.headers.get("Signature")

    if not cert_url or not signature_b64:
        logger.warning("Rejected Alexa request: missing Signature or SignatureCertChainUrl headers.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required Alexa signature headers."
        )

    if not is_valid_cert_url(cert_url):
        logger.warning(f"Rejected Alexa request: invalid cert URL '{cert_url}'.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SignatureCertChainUrl."
        )

    try:
        cert = await get_certificate(cert_url)
        public_key = cert.public_key()
        signature_bytes = base64.b64decode(signature_b64)

        # Alexa uses SHA-256 with PKCS#1 v1.5 padding
        public_key.verify(
            signature_bytes,
            raw_body,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except Exception as e:
        logger.error(f"Alexa cryptographic verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed cryptographic signature verification."
        )

