"""✨ Local-only. Draws the pages snap.py saved for a worktree as PNGs, at phone and desktop width, with the
worktree's own frontend build. Run through bin/screenshot, which uses the Playwright venv beside this folder.

Each page is loaded at http://snap.local/__page__/<name>, so its /static/ addresses resolve against the worktree's
frontend/dist (then frontend/img), as Django's static files would serve them. Anything else (a link's page, an
outside font) is refused, so a picture never depends on a server."""

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ORIGIN = "http://snap.local"


def static_file(worktree, rest):
    for folder in ("frontend/dist", "frontend/img"):
        path = worktree / folder / rest
        if path.is_file():
            return path
    return None


def main(worktree, folder, widths):
    pages = sorted(folder.glob("*.html"))
    if not pages:
        sys.exit(f"✗ no snapshots in {folder}: save some with snap.py first")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width in widths:
            context = browser.new_context(viewport={"width": width, "height": 900})

            def serve(route):
                url = route.request.url
                if url.startswith(f"{ORIGIN}/__page__/"):
                    page_path = folder / (url.rsplit("/", 1)[1] + ".html")
                    return route.fulfill(path=str(page_path), content_type="text/html")
                if url.startswith(f"{ORIGIN}/static/"):
                    path = static_file(worktree, url[len(f"{ORIGIN}/static/"):].split("?")[0])
                    if path:
                        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                        return route.fulfill(path=str(path), content_type=kind)
                return route.abort()

            context.route("**/*", serve)
            page = context.new_page()
            for html in pages:
                page.goto(f"{ORIGIN}/__page__/{html.stem}", wait_until="networkidle")
                out = folder / f"{html.stem}-{width}.png"
                selector = folder / f"{html.stem}.selector"
                if selector.exists():
                    page.locator(selector.read_text().strip()).first.screenshot(path=str(out))
                else:
                    page.screenshot(path=str(out), full_page=True)
                print(out)
            context.close()
        browser.close()


if __name__ == "__main__":
    worktree = Path(sys.argv[1]).resolve()
    folder = Path(sys.argv[2]).resolve()
    widths = [int(w) for w in sys.argv[3].split(",")]
    main(worktree, folder, widths)
