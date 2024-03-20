import os
import uuid
import hashlib


def generate_short_uid(uid: str = None):
    uid = uid or str(uuid.uuid4())
    hasher = hashlib.sha1(uid.encode())
    return hasher.hexdigest()[:8]
