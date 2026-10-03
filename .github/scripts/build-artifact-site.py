"""Package the standalone learning guides for GitHub Pages."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "artifact"
OUTPUT = ROOT / "_artifact_site"
REVISION = os.environ.get("GITHUB_SHA", "development")
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "orange-taco/traceback")
ATTRIBUTE = re.compile(r'(?P<name>\b(?:href|src))="(?P<url>[^"]+)"')


def published_url(page: Path, url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
        return url

    target = (page.parent / parsed.path).resolve()
    target.relative_to(ROOT)  # Reject links outside this repository.
    if not target.is_file():
        raise ValueError(f"Missing local link in {page}: {url}")
    if target.is_relative_to(SOURCE):
        return url

    repo_path = target.relative_to(ROOT).as_posix()
    suffix = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"https://github.com/{REPOSITORY}/blob/{REVISION}/{repo_path}{suffix}"


def rewrite_attributes(page: Path, content: str) -> str:
    def replace(match: re.Match[str]) -> str:
        url = published_url(page, match.group("url"))
        return f'{match.group("name")}="{url}"'

    return ATTRIBUTE.sub(replace, content)


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SOURCE, OUTPUT)
    (OUTPUT / ".nojekyll").touch()

    for page in SOURCE.glob("*.html"):
        content = rewrite_attributes(page, page.read_text(encoding="utf-8"))
        (OUTPUT / page.name).write_text(content, encoding="utf-8")

    print(f"Prepared {len(list(SOURCE.glob('*.html')))} guides in {OUTPUT}")


if __name__ == "__main__":
    main()
