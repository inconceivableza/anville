"""✨ Local-only. Saves a page as a test's client sees it, for bin/screenshot to draw, so a look change can be seen
without runserver (06, run 2: half its fixes were looks no agent had seen).

In a throwaway `snap_<name>.py` beside the journey tests (git ignores the pattern, and the suite never collects it,
pytest taking a file not named test_*.py only when it is named on the command line):

    import sys; sys.path.insert(0, "/Users/ryan/_Work/Inconceivable/Anville/.claude/tools/snapshot")
    from snap import snapshot
    from tests.journeys.test_hub import signed_in_client  # noqa: F401 (the fixture participant builds on)
    from tests.journeys.test_whatever_you_do import participant, through_section_1  # noqa: F401

Import every fixture the helpers' fixtures name, as the journey tests do; the helpers in the test modules
(through_section_1, submit_the_sort, answer_onboarding…) take a participant to any state.

    def test_hub(participant):  # noqa: F811
        through_section_1(participant)
        snapshot(participant, "/hub/", "hub-after-section-1", element=".slist")  # just the hub's rows

Run it as any test, then draw what it saved:

    cd <worktree> && MAIN/bin/pytest-expect --db <db> "all passed" tests/journeys/snap_<name>.py
    MAIN/bin/screenshot <worktree>
"""

from pathlib import Path

MAIN = Path("/Users/ryan/_Work/Inconceivable/Anville")


def snapshot_dir(worktree):
    """Where a worktree's snapshots go: under MAIN's .claude/ (ignored by git), never in the worktree itself."""
    return MAIN / ".claude" / "snapshots" / Path(worktree).name


def snapshot(client, url, name, element=None):
    """Save the page `client` gets at `url` (redirects followed) as `<name>.html`; returns its path. With `element`, a
    CSS selector, bin/screenshot draws only the first element it matches: a smaller picture, fewer tokens to read."""
    response = client.get(url, follow=True)
    folder = snapshot_dir(Path.cwd())
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.html"
    path.write_bytes(response.content)
    selector = folder / f"{name}.selector"
    if element:
        selector.write_text(element)
    elif selector.exists():
        selector.unlink()
    return path
