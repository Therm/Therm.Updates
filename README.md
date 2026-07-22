# Therm.Updates

Source for **updates.therm.energy** — Therm's public update streams. Everything in this
repository is world-readable; only headline-level, public-safe content belongs here.

## Streams

| Stream | Page | Feed |
|---|---|---|
| Release Notes | `/releases/` | `/releases/rss.xml` |
| Announcements | `/announcements/` | `/announcements/rss.xml` |
| Everything | `/` | `/rss.xml` |

## How it works

- Each entry is one markdown file in `updates/<stream>/`, named `YYYY-MM-DD-<slug>.md`,
  with `title`, `date`, and optional `link` front-matter and a one-paragraph description body.
- `generate.py` (stdlib-only Python) renders `site/` — HTML index pages plus RSS feeds.
- `.github/workflows/deploy.yml` builds and publishes to GitHub Pages on every push to `main`.

Release entries are appended automatically by the release-notes workflow in the
Docs.ReleaseNotes repository; the entry body must match that release's front-matter
`description` verbatim. Announcements are authored by hand.

## Content rules

- Titles, dates, and one-line descriptions only. Detailed content stays behind sign-in;
  entry links may point at authenticated pages (readers hit the sign-in wall by design).
- No ticket numbers, customer names, or internal system details — the same confidentiality
  bar as the published release notes.
- Never rename `rss.xml` paths or stream folders: feed URLs are customer subscriptions.
