#!/usr/bin/env python3
"""Build the static updates site (HTML + RSS) into site/ from updates/<stream>/*.md.

Each entry is a markdown file with YAML-ish front-matter:

    ---
    title: Energy Blocks, Bulk Tax Exemptions, and Contract Statuses
    date: 2026-07-21
    link: https://docs.therm.energy/release-notes/july-2026/21-july-...
    ---
    One-paragraph public-safe description.

Stdlib only — no dependencies.
"""
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
BASE_URL = "https://updates.therm.energy"

STREAMS = {
    "releases": {
        "title": "Release Notes",
        "blurb": (
            "Headline summaries of every Therm release, newest first. "
            "Full release notes live in the Therm documentation and require sign-in."
        ),
    },
    "announcements": {
        "title": "Announcements",
        "blurb": "Product and service announcements from the Therm team.",
    },
}

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.S)


def parse_entry(path):
    m = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"{path}: missing front-matter")
    meta = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    for required in ("title", "date"):
        if not meta.get(required):
            raise ValueError(f"{path}: missing '{required}'")
    date = datetime.strptime(meta["date"], "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    return {
        "title": meta["title"],
        "date": date,
        "link": meta.get("link", ""),
        "desc": " ".join(m.group(2).split()),
    }


def load_stream(name):
    folder = ROOT / "updates" / name
    entries = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.md")):
            entries.append(parse_entry(path))
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def rss(title, page_url, blurb, entries):
    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for e in entries:
        link = e["link"] or page_url
        items.append(
            "    <item>\n"
            f"      <title>{escape(e['title'])}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid isPermaLink=\"false\">{escape(link)}#{e['date']:%Y-%m-%d}</guid>\n"
            f"      <pubDate>{format_datetime(e['date'])}</pubDate>\n"
            f"      <description>{escape(e['desc'])}</description>\n"
            "    </item>"
        )
    body = "\n".join(items)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n"
        "  <channel>\n"
        f"    <title>{escape(title)}</title>\n"
        f"    <link>{escape(page_url)}</link>\n"
        f"    <description>{escape(blurb)}</description>\n"
        "    <language>en-us</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f"    <atom:link href=\"{escape(page_url.rstrip('/'))}/rss.xml\" rel=\"self\" type=\"application/rss+xml\"/>\n"
        f"{body}\n"
        "  </channel>\n"
        "</rss>\n"
    )


STYLE = """
:root { color-scheme: light dark; --fg: #1a1d21; --muted: #5c6570; --accent: #0b6bcb; --rule: #e3e6ea; --bg: #ffffff; }
@media (prefers-color-scheme: dark) { :root { --fg: #e8eaed; --muted: #9aa4af; --accent: #6cb2f7; --rule: #2c3238; --bg: #17191c; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 44rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
h2 { font-size: 1.1rem; margin: 0 0 .25rem; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
p { margin: .35rem 0; }
.muted { color: var(--muted); }
.entry, .stream { padding: 1.1rem 0; border-bottom: 1px solid var(--rule); }
.date { font-size: .85rem; color: var(--muted); }
.feed { font-size: .85rem; }
footer { margin-top: 2.5rem; font-size: .85rem; color: var(--muted); }
"""


def page(title, head_extra, body):
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{escape(title)}</title>\n"
        f"{head_extra}"
        f"<style>{STYLE}</style>\n"
        "</head>\n<body>\n<main>\n"
        f"{body}"
        "\n<footer>Published by <a href=\"https://therm.energy\">Therm</a>. "
        "Feeds on this site update automatically.</footer>\n"
        "</main>\n</body>\n</html>\n"
    )


def entry_html(e):
    title = (
        f"<a href=\"{escape(e['link'])}\">{escape(e['title'])}</a>"
        if e["link"] else escape(e["title"])
    )
    return (
        "<div class=\"entry\">\n"
        f"  <div class=\"date\">{e['date']:%d %B %Y}</div>\n"
        f"  <h2>{title}</h2>\n"
        f"  <p>{escape(e['desc'])}</p>\n"
        "</div>"
    )


def build():
    all_entries = []
    (OUT).mkdir(exist_ok=True)

    for name, cfg in STREAMS.items():
        entries = load_stream(name)
        all_entries.extend(entries)
        stream_url = f"{BASE_URL}/{name}/"
        out = OUT / name
        out.mkdir(parents=True, exist_ok=True)

        feed_title = f"Therm — {cfg['title']}"
        (out / "rss.xml").write_text(
            rss(feed_title, stream_url, cfg["blurb"], entries), encoding="utf-8"
        )

        alternate = (
            f"<link rel=\"alternate\" type=\"application/rss+xml\" "
            f"title=\"{escape(feed_title)}\" href=\"{stream_url}rss.xml\">\n"
        )
        listing = "\n".join(entry_html(e) for e in entries) or (
            "<p class=\"muted\">Nothing here yet.</p>"
        )
        body = (
            f"<p class=\"feed\"><a href=\"{BASE_URL}/\">Therm Updates</a> / {escape(cfg['title'])}</p>\n"
            f"<h1>{escape(cfg['title'])}</h1>\n"
            f"<p class=\"muted\">{escape(cfg['blurb'])}</p>\n"
            f"<p class=\"feed\">Subscribe: <a href=\"{stream_url}rss.xml\">RSS feed</a></p>\n"
            f"{listing}"
        )
        (out / "index.html").write_text(page(feed_title, alternate, body), encoding="utf-8")

    all_entries.sort(key=lambda e: e["date"], reverse=True)
    combined_title = "Therm — All Updates"
    (OUT / "rss.xml").write_text(
        rss(combined_title, f"{BASE_URL}/", "All public Therm update streams.", all_entries),
        encoding="utf-8",
    )

    streams_html = "\n".join(
        "<div class=\"stream\">\n"
        f"  <h2><a href=\"{BASE_URL}/{name}/\">{escape(cfg['title'])}</a></h2>\n"
        f"  <p class=\"muted\">{escape(cfg['blurb'])}</p>\n"
        f"  <p class=\"feed\"><a href=\"{BASE_URL}/{name}/rss.xml\">RSS feed</a></p>\n"
        "</div>"
        for name, cfg in STREAMS.items()
    )
    alternate = (
        f"<link rel=\"alternate\" type=\"application/rss+xml\" "
        f"title=\"{escape(combined_title)}\" href=\"{BASE_URL}/rss.xml\">\n"
    )
    body = (
        "<h1>Therm Updates</h1>\n"
        "<p class=\"muted\">Public update streams from Therm. Subscribe to a stream below, "
        f"or to <a href=\"{BASE_URL}/rss.xml\">everything at once</a>.</p>\n"
        f"{streams_html}"
    )
    (OUT / "index.html").write_text(page("Therm Updates", alternate, body), encoding="utf-8")
    print(f"built {sum(1 for _ in OUT.rglob('*') if _.is_file())} files into {OUT}")


if __name__ == "__main__":
    build()
