import secrets
import hashlib

PREFIX = "gw_live_"

def generate_api_key() -> str:
    """Generate a random API key."""
    return PREFIX + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash the API key using SHA256."""
    
    return hashlib.sha256(api_key.encode()).hexdigest()