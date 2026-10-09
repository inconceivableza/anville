"""✨ Fake but plausible assessments for the seeding commands (`seed_observers`, `seed_cohort`): the same on every run,
and never made for a real participant."""

import hashlib


def self_assessment(document, seed=None):
    """✨ Every item placed in a bucket picked by a hash of the item (and of `seed`, if given, so that seeded
    participants differ), at the bucket's seed value, as if its slider were left untouched. Uneven enough that the
    self-result is not flat."""
    buckets = document["instrument"]["buckets"]
    prefix = (seed,) if seed else ()
    return {
        item["id"]: _placement(buckets, stable_number(*prefix, item["id"], "self") % len(buckets))
        for item in document["instrument"]["items"]
    }


def observer_assessment(document, assessment, number):
    """✨ The self-assessment with each item moved by at most one bucket either way, as someone who knows the
    participant well might see them: close enough to agree mostly, different enough to show gaps."""
    buckets = document["instrument"]["buckets"]
    positions = {bucket["id"]: position for position, bucket in enumerate(buckets)}
    moved = {}
    for item_id, placement in assessment.items():
        position = positions[placement["bucket"]] + stable_number(item_id, f"observer-{number}") % 3 - 1
        moved[item_id] = _placement(buckets, min(max(position, 0), len(buckets) - 1))
    return moved


def _placement(buckets, position):
    return {"bucket": buckets[position]["id"], "value": buckets[position]["seed"]}


def stable_number(*parts):
    """✨ A number from the parts that is the same every run. Python's hash() of a string changes between runs."""
    return int(hashlib.sha256("/".join(parts).encode()).hexdigest(), 16)
