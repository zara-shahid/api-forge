import uuid


def new_api_id() -> str:
    """Short, URL-friendly unique id for a generated API."""
    return uuid.uuid4().hex[:8]
