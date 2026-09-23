"""✨ Pathway documents for tests, built fresh on each call so a test can alter its copy freely."""


def scripture_reading(**fields):
    """✨ A scripture reading block, with its authored parts overridable one at a time."""
    return {
        "id": "reading",
        "type": "scripture_reading",
        "heading": "Read these first",
        "passages": [{"reference": "1 Corinthians 12:4-11", "text": "There are different kinds of gifts."}],
        "note": "Read slowly, and notice what stays with you.",
        "confirm_label": "I have read these",
        **fields,
    }


def pathway_document():
    return {
        "format": 1,
        "title": "Test Pathway",
        "content": {
            "sections": [
                {
                    "id": "onboarding",
                    "title": "Before we begin",
                    "blocks": [
                        {"id": "welcome", "type": "rich_text", "body": "Welcome to the pathway."},
                        {
                            "id": "baseline-bible",
                            "type": "agreement_scale",
                            "prompt": "I understand what the Bible teaches about work.",
                            "min_label": "Strongly disagree",
                            "max_label": "Strongly agree",
                        },
                    ],
                },
                {
                    "id": "calling",
                    "title": "Putting your calling into words",
                    "requires": ["onboarding"],
                    "blocks": [
                        {
                            "id": "statement",
                            "type": "long_text",
                            "prompt": {"participant": "Write your statement.", "observer": ""},
                        },
                    ],
                    "gate": {
                        "clauses": [
                            {
                                "type": "min_text_length",
                                "block": "statement",
                                "min": 10,
                                "message": "Write a statement of at least ten characters.",
                            },
                        ],
                    },
                },
            ],
        },
        "instrument": {
            "buckets": [
                {"id": "not-me", "label": "Not me", "seed": 10},
                {"id": "strength", "label": "Real strength", "seed": 85},
            ],
            "items": [
                {
                    "id": "a5",
                    "text": {
                        "participant": "Building something that will outlast you",
                        "observer": "Building something that will outlast them",
                    },
                    "loads": ["apostle", "deliver"],
                },
            ],
        },
        "measurement": {
            "frameworks": [
                {"id": "apest", "label": "APEST(d)", "constructs": [{"id": "apostle", "label": "Apostle"}]},
                {"id": "pep", "label": "PEP", "constructs": [{"id": "deliver", "label": "Deliver"}]},
            ],
        },
        "presentation": {
            "constructs": [{"construct": "apostle", "description": "Pioneers new things."}],
            "disclaimer": "These results are indicative, not definitive.",
        },
    }
