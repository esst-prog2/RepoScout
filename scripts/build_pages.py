"""Assemble RepoScout's GitHub Pages site: the promo page at the root, the web
app under app/. The same folder is previewed locally and deployed, so what you
preview is what gets published.

    python scripts/build_pages.py                 # build into _site/ (version "dev")
    python scripts/build_pages.py --serve         # build, then serve on http://localhost:8000
    python scripts/build_pages.py --version abc1234

Only copies are changed: stylesheet and script links and the app's module
imports get a ?v=<version> suffix, so a browser never mixes an old cached file
with a new one. promo/ and site/ are only read. Standard library only.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Screenshots the promo page uses whole, copied from docs/screenshots/ into img/.
# None at the moment: the page shows crops committed in promo/img/ (see its
# README.md), because whole screenshots can't be read at the size shown.
# Screenshot 4 (the table) must never be added here: its account names can be
# real names, so the page uses promo/img/table-csv.png, a blurred copy.
SCREENSHOTS: dict[str, str] = {}

# Files in promo/ that document how the assets were made; never published.
PROMO_EXCLUDE = {"img/README.md"}

VERSION_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
TAG_RE = re.compile(r"<(link|script)\b[^>]*>", re.IGNORECASE)
ATTR_RE = r'(\b{name}\s*=\s*")([^"]*)(")'
IMPORT_RE = re.compile(r"""(\b(?:from|import)\s*["'])(\.{1,2}/[^"'?#]+\.m?js)(["'])""")
TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".txt", ".md", ".json", ".svg"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LOCAL_PATH_RE = re.compile(r"\b[A-Za-z]:\\|/home/|/Users/")


class BuildError(Exception):
    """The site can't be assembled safely; nothing should be deployed."""


def _is_relative(url: str) -> bool:
    return bool(url) and not re.match(r"^([a-z][a-z0-9+.-]*:|//|/|#)", url, re.IGNORECASE)


def _bustable(tag: str) -> str | None:
    """The attribute to suffix in a <link>/<script> tag, or None (fonts, icons...)."""
    if tag.lower().startswith("<script"):
        return "src"
    rel = re.search(ATTR_RE.format(name="rel"), tag, re.IGNORECASE)
    return "href" if rel and "stylesheet" in rel.group(2).lower().split() else None


def bust_html(html: str, version: str) -> str:
    def fix(match: re.Match) -> str:
        tag = match.group(0)
        attr = _bustable(tag)
        if attr is None:
            return tag

        def add(m: re.Match) -> str:
            url = m.group(2)
            if not _is_relative(url) or "?" in url:
                return m.group(0)
            return f"{m.group(1)}{url}?v={version}{m.group(3)}"

        return re.sub(ATTR_RE.format(name=attr), add, tag, count=1, flags=re.IGNORECASE)

    return TAG_RE.sub(fix, html)


def bust_js(js: str, version: str) -> str:
    return IMPORT_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}?v={version}{m.group(3)}", js)


def _own_js(folder: Path):
    """JavaScript we wrote (vendored libraries are left byte-for-byte)."""
    return [p for p in folder.rglob("*.js") if "vendor" not in p.relative_to(folder).parts]


def check_cache_busting(folder: Path) -> None:
    """Fail if any relative stylesheet/script link or module import lacks ?v=."""
    missing = []
    for page in folder.rglob("*.html"):
        for match in TAG_RE.finditer(page.read_text(encoding="utf-8")):
            tag = match.group(0)
            attr = _bustable(tag)
            url = re.search(ATTR_RE.format(name=attr), tag, re.IGNORECASE) if attr else None
            if url and _is_relative(url.group(2)) and "?v=" not in url.group(2):
                missing.append(f"{page.relative_to(folder).as_posix()}: {url.group(2)}")
    for script in _own_js(folder):
        for match in IMPORT_RE.finditer(script.read_text(encoding="utf-8")):
            missing.append(f"{script.relative_to(folder).as_posix()}: import {match.group(2)}")
    if missing:
        raise BuildError("not cache-busted: " + "; ".join(missing))


def check_personal_data(folder: Path) -> None:
    """Fail if a published text file holds an e-mail address or a local path."""
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(folder).as_posix()
            if EMAIL_RE.search(text):
                raise BuildError(f"e-mail address in published file {rel}")
            if LOCAL_PATH_RE.search(text):
                raise BuildError(f"local path in published file {rel}")


def _check_output(root: Path, out: Path) -> None:
    root, out = root.resolve(), out.resolve()
    if out == root or out in root.parents:
        raise BuildError(f"refusing to build into {out}: it contains the repository")
    for protected in ("site", "promo", "docs", "scripts", "tests", "reposcout", "openspec", ".git", ".github"):
        p = (root / protected).resolve()
        if out == p or p in out.parents:
            raise BuildError(f"refusing to build into {out}: it is inside {protected}/")
    if out.exists():
        if not out.is_dir():
            raise BuildError(f"refusing to replace {out}: it is a file")
        entries = list(out.iterdir())
        looks_built = (out / "index.html").is_file() and (out / "app").is_dir()
        if entries and not looks_built:
            raise BuildError(f"refusing to wipe {out}: it is not empty and not a previous build")


def build(root: Path, out: Path, version: str) -> Path:
    if not VERSION_RE.match(version or ""):
        raise BuildError(f"version must be letters, digits, '-' or '_' (got {version!r})")
    root = Path(root).resolve()
    out = Path(out).resolve()
    _check_output(root, out)
    if out.exists():
        shutil.rmtree(out)

    promo = root / "promo"
    for src in promo.rglob("*"):
        rel = src.relative_to(promo).as_posix()
        if src.is_file() and rel not in PROMO_EXCLUDE:
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
    for name, target in SCREENSHOTS.items():
        dest = out / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "docs" / "screenshots" / name, dest)
    shutil.copytree(root / "site", out / "app")

    for page in out.rglob("*.html"):
        page.write_text(bust_html(page.read_text(encoding="utf-8"), version), encoding="utf-8", newline="")
    for script in _own_js(out):
        script.write_text(bust_js(script.read_text(encoding="utf-8"), version), encoding="utf-8", newline="")

    check_cache_busting(out)
    check_personal_data(out)
    return out


def serve(folder: Path, port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {folder} at http://localhost:{port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(REPO / "_site"), help="output folder (default: _site)")
    parser.add_argument("--version", default="dev", help="cache-busting suffix, e.g. a short commit SHA")
    parser.add_argument("--serve", nargs="?", type=int, const=8000, metavar="PORT",
                        help="serve the built folder for a local preview (default port 8000)")
    args = parser.parse_args(argv)
    try:
        out = build(REPO, Path(args.out), args.version)
    except BuildError as error:
        print(f"build_pages: {error}", file=sys.stderr)
        return 1
    print(f"Built {out}")
    if args.serve is not None:
        serve(out, args.serve)
    return 0


if __name__ == "__main__":
    sys.exit(main())
