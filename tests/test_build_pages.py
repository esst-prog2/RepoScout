"""Tests for scripts/build_pages.py, the one assembly used for the local preview
and the GitHub Pages deploy (openspec change promo-page-on-github-pages)."""

import hashlib
import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("build_pages", REPO / "scripts" / "build_pages.py")
build_pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_pages)


# --- a small fake repository, so the assembly rules are tested on their own ---

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def fake_repo(tmp_path):
    root = tmp_path / "repo"
    _write(root / "site" / "index.html",
           '<link rel="preload" href="vendor/fonts/f.woff2" as="font" type="font/woff2" crossorigin>\n'
           '<link rel="stylesheet" href="style.css">\n'
           '<script src="vendor/d3.min.js"></script>\n'
           '<script type="module" src="app.js"></script>\n')
    _write(root / "site" / "style.css", '@font-face { src: url(vendor/fonts/f.woff2) format("woff2"); }\n')
    _write(root / "site" / "app.js", 'import { a, b } from "./rules.js";\nconsole.log(a, b);\n')
    _write(root / "site" / "rules.js", "export const a = 1;\nexport const b = 2;\n")
    _write(root / "site" / "vendor" / "d3.min.js", "/* d3 */\n")
    (root / "site" / "vendor" / "fonts").mkdir(parents=True)
    (root / "site" / "vendor" / "fonts" / "f.woff2").write_bytes(b"\x00font")
    _write(root / "promo" / "index.html",
           '<link rel="stylesheet" href="style.css">\n<a href="app/">Open RepoScout</a>\n')
    _write(root / "promo" / "style.css", '@font-face { src: url(app/vendor/fonts/f.woff2); }\n')
    _write(root / "promo" / "img" / "README.md", "how the crops were made\n")
    (root / "promo" / "img" / "lead.png").write_bytes(b"\x89PNG")
    (root / "docs" / "screenshots").mkdir(parents=True)
    for name in build_pages.SCREENSHOTS:
        (root / "docs" / "screenshots" / name).write_bytes(b"\x89PNG")
    (root / "docs" / "screenshots" / "4-table-csv-project-management-software.png").write_bytes(b"\x89PNG")
    _write(root / "AGENTS.md", "planning log\n")
    _write(root / "PRODUCT.md", "product\n")
    _write(root / "pyproject.toml", "[project]\n")
    _write(root / "tests" / "test_x.py", "")
    _write(root / "openspec" / "specs" / "x.md", "")
    _write(root / "reposcout" / "cli.py", "")
    _write(root / ".impeccable" / "design.json", "{}")
    return root


def _files(folder: Path) -> set[str]:
    return {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}


def _digest(folder: Path) -> dict[str, str]:
    return {rel: hashlib.sha256((folder / rel).read_bytes()).hexdigest() for rel in _files(folder)}


def test_layout_is_promo_at_root_and_app_under_app(fake_repo):
    out = fake_repo / "_site"
    build_pages.build(fake_repo, out, "abc1234")
    expected = {"index.html", "style.css", "img/lead.png"}
    expected |= set(build_pages.SCREENSHOTS.values())
    expected |= {"app/" + rel for rel in _files(fake_repo / "site")}
    assert _files(out) == expected


def test_nothing_else_from_the_repo_is_published(fake_repo):
    out = fake_repo / "_site"
    build_pages.build(fake_repo, out, "abc1234")
    published = _files(out)
    for forbidden in ("AGENTS.md", "PRODUCT.md", "pyproject.toml", "img/README.md", "README.md"):
        assert forbidden not in published
    assert not any(p.startswith(("tests/", "openspec/", "reposcout/", ".impeccable/", "docs/")) for p in published)
    assert not any("4-table-csv" in p for p in published)


def test_stylesheets_scripts_and_rules_import_are_suffixed(fake_repo):
    out = fake_repo / "_site"
    build_pages.build(fake_repo, out, "abc1234")
    app_html = (out / "app" / "index.html").read_text(encoding="utf-8")
    assert 'href="style.css?v=abc1234"' in app_html
    assert 'src="vendor/d3.min.js?v=abc1234"' in app_html
    assert 'src="app.js?v=abc1234"' in app_html
    assert 'from "./rules.js?v=abc1234"' in (out / "app" / "app.js").read_text(encoding="utf-8")
    assert 'href="style.css?v=abc1234"' in (out / "index.html").read_text(encoding="utf-8")


def test_fonts_are_not_suffixed(fake_repo):
    out = fake_repo / "_site"
    build_pages.build(fake_repo, out, "abc1234")
    assert 'href="vendor/fonts/f.woff2" as="font"' in (out / "app" / "index.html").read_text(encoding="utf-8")
    assert "url(vendor/fonts/f.woff2)" in (out / "app" / "style.css").read_text(encoding="utf-8")
    assert "url(app/vendor/fonts/f.woff2)" in (out / "style.css").read_text(encoding="utf-8")


def test_sources_are_never_modified(fake_repo):
    before = {name: _digest(fake_repo / name) for name in ("site", "promo")}
    build_pages.build(fake_repo, fake_repo / "_site", "abc1234")
    assert {name: _digest(fake_repo / name) for name in ("site", "promo")} == before


def test_rebuild_replaces_a_previous_build(fake_repo):
    out = fake_repo / "_site"
    build_pages.build(fake_repo, out, "old0001")
    (out / "stale.txt").write_text("left over", encoding="utf-8")
    build_pages.build(fake_repo, out, "new0002")
    assert not (out / "stale.txt").exists()
    assert "?v=new0002" in (out / "index.html").read_text(encoding="utf-8")


def test_check_fails_on_an_unsuffixed_link(tmp_path):
    _write(tmp_path / "index.html", '<link rel="stylesheet" href="style.css">\n')
    with pytest.raises(build_pages.BuildError, match="style.css"):
        build_pages.check_cache_busting(tmp_path)


def test_check_fails_on_an_unsuffixed_rules_import(tmp_path):
    _write(tmp_path / "app" / "app.js", 'import { a } from "./rules.js";\n')
    with pytest.raises(build_pages.BuildError, match="rules.js"):
        build_pages.check_cache_busting(tmp_path)


def test_check_passes_on_suffixed_files(tmp_path):
    _write(tmp_path / "index.html", '<link rel="stylesheet" href="style.css?v=1">\n<script src="a.js?v=1"></script>\n')
    _write(tmp_path / "app" / "app.js", 'import { a } from "./rules.js?v=1";\n')
    build_pages.check_cache_busting(tmp_path)


def test_external_urls_are_left_alone():
    html = '<link rel="stylesheet" href="https://example.org/x.css">\n<script src="//cdn.example/y.js"></script>\n'
    assert build_pages.bust_html(html, "abc1234") == html


@pytest.mark.parametrize("bad", ["", "a b", "x;rm", "../v", "v?1"])
def test_version_must_be_a_plain_token(fake_repo, bad):
    with pytest.raises(build_pages.BuildError):
        build_pages.build(fake_repo, fake_repo / "_site", bad)


@pytest.mark.parametrize("target", [".", "site", "promo", "site/sub", "docs", ".."])
def test_refuses_dangerous_output_folders(fake_repo, target):
    with pytest.raises(build_pages.BuildError):
        build_pages.build(fake_repo, (fake_repo / target).resolve(), "abc1234")


def test_refuses_to_wipe_a_folder_that_is_not_a_previous_build(fake_repo):
    out = fake_repo / "notes"
    _write(out / "mine.txt", "keep me")
    with pytest.raises(build_pages.BuildError):
        build_pages.build(fake_repo, out, "abc1234")
    assert (out / "mine.txt").exists()


def test_personal_data_in_a_published_text_file_fails_the_build(fake_repo):
    _write(fake_repo / "promo" / "index.html", "<p>write to someone@example.com</p>\n")
    with pytest.raises(build_pages.BuildError, match="e-mail"):
        build_pages.build(fake_repo, fake_repo / "_site", "abc1234")


def test_local_path_in_a_published_text_file_fails_the_build(fake_repo):
    _write(fake_repo / "promo" / "style.css", "/* C:\\Users\\someone\\x.css */\n")
    with pytest.raises(build_pages.BuildError, match="local path"):
        build_pages.build(fake_repo, fake_repo / "_site", "abc1234")


# --- the real repository: the assembled site as it will be published ---

@pytest.fixture(scope="module")
def real_site(tmp_path_factory):
    out = tmp_path_factory.mktemp("pages") / "_site"
    build_pages.build(REPO, out, "test123")
    return out


def test_real_site_has_no_personal_data_and_no_original_table_screenshot(real_site):
    email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    for rel in _files(real_site):
        assert "4-table-csv" not in rel
        if rel.endswith((".html", ".css", ".js", ".txt", ".md", ".json")):
            text = (real_site / rel).read_text(encoding="utf-8", errors="replace")
            assert not email.search(text), rel
            assert not re.search(r"[A-Za-z]:\\|/home/|/Users/", text), rel


def _promo_text(real_site) -> str:
    """The promo page's visible text, tags removed and whitespace collapsed."""
    html = (real_site / "index.html").read_text(encoding="utf-8")
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def test_promo_quotes_the_26_october_verdicts_exactly(real_site):
    text = _promo_text(real_site)
    for verdict in (
        "Showing the 50 best-matching of 177,486 repos, 37 active among them — most recent entrant pushed 3 minutes ago",
        "Showing the 50 best-matching of 3,137 repos, 0 active among them — most recent entrant pushed 3 months ago",
        "Showing the 50 best-matching of 14,067 repos, 10 active among them — most recent entrant pushed 1 minute ago",
    ):
        assert verdict in text
    assert "26 October 2026" in text
    assert "5 landed in a different group" in text


def test_promo_has_the_three_answers_and_the_limits(real_site):
    text = _promo_text(real_site)
    for heading in ("Is your idea's corner of GitHub alive?", "For people about to build",
                    "One search, four answers", "Try it", "In your browser", "On the command line", "Honest limits"):
        assert heading in text
    for command in ("git clone https://github.com/esst-prog2/RepoScout", "python -m venv .venv",
                    "pip install .", 'reposcout search "project management software"'):
        assert command in text
    # PowerShell blocks activation scripts by default, so the Windows block
    # must work without .venv\Scripts\activate (critique round 2).
    assert "Scripts\\activate" not in text


def test_promo_links_to_the_app_the_code_and_the_manual(real_site):
    html = (real_site / "index.html").read_text(encoding="utf-8")
    links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
    assert ("app/", "Open RepoScout") in links
    assert ("https://github.com/esst-prog2/RepoScout", "View the code on GitHub") in links
    assert any(href.endswith("/docs/USER_MANUAL.md") for href, _ in links)
    primaries = re.findall(r'<a\b[^>]*class="button primary"[^>]*>', html)
    assert primaries and all('href="app/"' in tag for tag in primaries)  # one primary action: open the app


def test_promo_makes_no_hype_claims(real_site):
    text = _promo_text(real_site)
    assert "!" not in text
    for word in ("blazing", "powerful", "the best", "trusted by", "testimonial", "revolutionary"):
        assert word not in text.lower()


def test_every_promo_image_exists_and_has_alt_text(real_site):
    html = (real_site / "index.html").read_text(encoding="utf-8")
    images = re.findall(r"<img\b[^>]*>", html, flags=re.S)
    assert len(images) == 4
    for tag in images:
        src = re.search(r'src="([^"]+)"', tag).group(1)
        alt = re.search(r'alt="([^"]*)"', tag).group(1)
        assert (real_site / src).is_file(), src
        assert len(alt) > 40, src


def test_real_site_app_matches_site_folder(real_site):
    assert {p for p in _files(real_site) if p.startswith("app/")} == {"app/" + p for p in _files(REPO / "site")}
