import json
from io import StringIO

import pytest
from django.core.management import call_command


@pytest.fixture
def load_pathway(tmp_path):
    """✨ Write a pathway document to a file and load it the way an author does; returns the command's output."""

    def load(document, *, name="pathway.json", indent=None):
        path = tmp_path / name
        path.write_text(json.dumps(document, indent=indent))
        out = StringIO()
        call_command("load_pathway", str(path), stdout=out)
        return out.getvalue()

    return load
