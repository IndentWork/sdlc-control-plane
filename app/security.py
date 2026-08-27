"""
Cryptographic helpers shared across the app.
Keeps hashing logic in one place — routers, migrations, and tests can all use it.
"""
import hashlib


def hash_key(plaintext: str) -> str:
    """
    SHA256 hash of a plaintext tenant key.
    This is the ONLY form of the key that gets stored in the database.
    Same input always produces the same output — safe for equality lookups.
    """
    return hashlib.sha256(plaintext.encode()).hexdigest()
