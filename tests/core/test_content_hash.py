import json

from engine.document import content_hash
from tests.documents import pathway_document


def test_a_content_hash_is_the_sha256_of_compact_json_with_sorted_keys():
    # ✨ Expected digest computed independently: printf '{"format":1}' | shasum -a 256
    assert content_hash({"format": 1}) == "3f0a99256beeb89a6b9f2793885291a6454928fd74903159ab2e51452b13df6f"


def test_the_same_content_hashes_the_same_whatever_its_layout_in_the_file():
    document = pathway_document()
    reordered = json.loads(json.dumps(document, sort_keys=True, indent=4))

    assert content_hash(reordered) == content_hash(document)


def test_changing_one_prompt_changes_the_hash():
    document = pathway_document()
    edited = pathway_document()
    edited["content"]["sections"][0]["blocks"][0]["body"] = "Welcome, friend."

    assert content_hash(edited) != content_hash(document)
