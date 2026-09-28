import hashlib
import hmac
from ipaddress import ip_address
from urllib.parse import urlparse

import requests
from django.conf import settings

from .base import ProviderError


TIMEOUT = (5, 30)
TEMPORARY_META_CODES = {1, 2, 4, 17, 32, 613}


def graph_url(path):
    return f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/{path.lstrip('/')}"


def post_graph(path, *, token, payload):
    if not token:
        raise ProviderError("Meta provider is not configured.", retryable=False)
    try:
        response = requests.post(
            graph_url(path),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT,
        )
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise ProviderError("Meta is temporarily unreachable.", retryable=True) from exc
    except requests.RequestException as exc:
        raise ProviderError("Meta request failed.", retryable=True) from exc

    try:
        data = response.json()
    except (TypeError, ValueError) as exc:
        raise ProviderError(
            "Meta returned an unreadable response.", retryable=response.status_code >= 500, status_code=response.status_code
        ) from exc
    if response.status_code >= 400 or "error" in data:
        error = data.get("error") if isinstance(data, dict) else {}
        error = error if isinstance(error, dict) else {}
        code = error.get("code")
        retryable = response.status_code == 429 or response.status_code >= 500 or code in TEMPORARY_META_CODES
        raise ProviderError(
            "Meta temporarily rejected the request." if retryable else "Meta rejected the request.",
            retryable=retryable,
            status_code=response.status_code,
            safe_details={key: error[key] for key in ("code", "type", "error_subcode") if key in error},
        )
    return data


def is_public_https_url(value):
    try:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname:
            return False
        hostname = parsed.hostname.lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
            return False
        try:
            address = ip_address(hostname)
        except ValueError:
            return True
        return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved)
    except (TypeError, ValueError):
        return False


def validate_meta_signature(*, raw_body, signature_header):
    secret = getattr(settings, "META_APP_SECRET", "")
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    supplied = signature_header.removeprefix("sha256=")
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)
