"""Check one chart week's saved files and record their hashes.

Usage:
    python tools/log_week.py 2026-11-21

The argument is the Hot 100 chart date, which is a Saturday. The tracking
week is the Friday-to-Thursday week ending nine days earlier.

Expected files, all under data/<chart date>/ :
    hot100.csv                 rank,title,artist              (40+ rows)
    public_forecast.csv        predicted_rank,title,artist,
                               source,posted_at,url           (20+ rows)
    spotify_us/<YYYY-MM-DD>.csv  one per tracking day, with rank,
                               track, artist and streams columns (150+ rows)

Nothing is written unless every check passes. Raw files stay in data/,
which git ignores. Only their SHA-256 hashes go into log/manifest.csv.
"""

import csv
import hashlib
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "log" / "manifest.csv"
MANIFEST_COLS = ["chart_date", "file", "rows", "sha256", "logged_at_utc"]

# Accepted header names, lower-cased. Spotify's own export and other
# sources name the track and artist columns differently.
TRACK_NAMES = {"track_name", "title", "track", "song"}
ARTIST_NAMES = {"artist_names", "artist", "artists"}


def tracking_days(chart_date: date) -> list[date]:
    """Friday through Thursday, ending nine days before the chart date."""
    end = chart_date - timedelta(days=9)
    return [end - timedelta(days=6 - i) for i in range(7)]


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = [h.strip().lower() for h in (reader.fieldnames or [])]
        rows = [r for r in reader if any((v or "").strip() for v in r.values())]
    return header, rows


def check(path: Path, required: list[set[str]], min_rows: int) -> tuple[int, list[str]]:
    """Return (row count, problems). Each item in `required` is a set of
    acceptable names for one column."""
    if not path.exists():
        return 0, [f"missing: {path.relative_to(ROOT)}"]
    header, rows = read_rows(path)
    problems = []
    for names in required:
        if not names & set(header):
            problems.append(
                f"{path.relative_to(ROOT)}: no column named any of {sorted(names)}"
            )
    if len(rows) < min_rows:
        problems.append(
            f"{path.relative_to(ROOT)}: {len(rows)} rows, need at least {min_rows}"
        )
    return len(rows), problems


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def already_logged(chart_date: str) -> bool:
    if not MANIFEST.exists():
        return False
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return any(r["chart_date"] == chart_date for r in csv.DictReader(f))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        chart_date = date.fromisoformat(sys.argv[1])
    except ValueError:
        print(f"Not a date: {sys.argv[1]}. Use YYYY-MM-DD.")
        return 2
    if chart_date.weekday() != 5:
        print(f"{chart_date} is not a Saturday. Hot 100 chart dates are Saturdays.")
        return 2
    if already_logged(str(chart_date)):
        print(f"{chart_date} is already in the manifest. Logged weeks are not rewritten.")
        return 1

    week_dir = ROOT / "data" / str(chart_date)
    days = tracking_days(chart_date)
    print(f"Chart {chart_date}: tracking week {days[0]} to {days[-1]}")

    files = [
        (week_dir / "hot100.csv", [{"rank"}, TRACK_NAMES, ARTIST_NAMES], 40),
        (
            week_dir / "public_forecast.csv",
            [{"predicted_rank"}, TRACK_NAMES, ARTIST_NAMES, {"source"}, {"posted_at"}, {"url"}],
            20,
        ),
    ]
    for d in days:
        files.append(
            (
                week_dir / "spotify_us" / f"{d}.csv",
                [{"rank"}, TRACK_NAMES, ARTIST_NAMES, {"streams"}],
                150,
            )
        )

    entries, problems = [], []
    for path, required, min_rows in files:
        n, found = check(path, required, min_rows)
        problems.extend(found)
        if not found:
            entries.append((path, n))

    # Two tracking days with identical contents means a file was saved twice.
    seen = {}
    for path, _ in entries:
        if path.parent.name == "spotify_us":
            h = sha256(path)
            if h in seen:
                problems.append(f"{path.name} is identical to {seen[h]}: same day saved twice?")
            seen[h] = path.name

    if problems:
        print("\nNot logged. Fix these first:")
        for p in problems:
            print(f"  - {p}")
        return 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_file = not MANIFEST.exists()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(MANIFEST_COLS)
        for path, n in entries:
            w.writerow([chart_date, path.relative_to(week_dir).as_posix(), n, sha256(path), now])

    print(f"Logged {len(entries)} files. Now commit log/manifest.csv.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
