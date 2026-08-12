"""Release Notes API — demo workload for Supply Chain Security Patterns for Cloud Delivery.

Deliberately tiny. The interesting part for the demo is not the app,
it's that the API key is fetched from Secrets Manager at runtime via the
Lambda execution role — never baked into the image, config, or source.
"""

import json
import os
import time

import boto3

SECRET_ID = os.environ.get("API_KEY_SECRET_ID", "demo/release-notes/api-key")

_cached_secret = None


def _get_api_key():
    """Fetch the secret at the moment of use (Clip 4, slide 9 pattern)."""
    global _cached_secret
    if _cached_secret is None:
        sm = boto3.client("secretsmanager")
        resp = sm.get_secret_value(SecretId=SECRET_ID)
        _cached_secret = resp["SecretString"]
    return _cached_secret


RELEASE_NOTES = [
    {"version": "1.2.0", "note": "Added artifact signing to the release path."},
    {"version": "1.1.0", "note": "Dependencies now pinned and verified byte-for-byte."},
    {"version": "1.0.0", "note": "Initial release via the secured pipeline."},
]


def mask(value: str) -> str:
    """Show proof the secret was retrieved without ever printing it."""
    if not value or len(value) < 8:
        return "********"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def handler(event, context):
    key = _get_api_key()
    body = {
        "service": "release-notes-api",
        "image_digest_env": os.environ.get("IMAGE_DIGEST", "unknown"),
        "secret_retrieved_at_runtime": True,
        "api_key_masked": mask(key),
        "timestamp": int(time.time()),
        "release_notes": RELEASE_NOTES,
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, indent=2),
    }
