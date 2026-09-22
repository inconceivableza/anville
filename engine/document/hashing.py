import hashlib
import json


def content_hash(document):
    """✨ SHA-256 of the document as compact, key-sorted UTF-8 JSON, so file layout never matters.

    Stored against every pathway version: changing this definition would orphan every stored hash.
    """
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
