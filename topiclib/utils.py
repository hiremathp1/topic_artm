import hashlib

def hash_text(text: str) -> str:
    """Returns a hash of the given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
