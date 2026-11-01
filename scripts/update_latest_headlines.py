"""Check NSO's latest English releases and refresh verified homepage indicators.

The archive and article prose are checked daily. A value is only replaced when a
label-specific parser finds the expected value and reference period; otherwise
the previous verified value remains in place for review.
"""
from datetime import date, timedelta
from pathlib import Path
import html
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request

ARCHIVES = {
    "monthly-report": "Socio-economic reports",
    "cpi": "CPI, gold & USD indexes",
    "iip": "Index of Industrial Production",
    "import-export": "Preliminary Exports and Imports",
}

ROOT = Path(__file__).resolve().parents[1]
HEADLINES = ROOT / "public" / "webdata" / "latest-headlines.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VietnamStatisticsExplorer/1.0)"}
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def fetch(url):
    request = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&%+"), headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def archive(archive_slug, start):
    rows = []
    page = 1
    while page <= 15:
        url = f"https://www.nso.gov.vn/en/{archive_slug}/" + (f"?paged={page}" if page > 1 else "")
        raw = fetch(url).decode("utf-8", errors="replace")
        entries = re.findall(
            r'<a\s+href=["\']([^"\']+)["\'][^>]*>\s*(?:</p>\s*)?<section class="item">(.*?)</section>',
            raw, re.S | re.I,
        )
        if not entries:
            raise ValueError(f"NSO archive format changed or returned no entries: {url}")
        dates = []
        for link, body in entries:
            title = re.search(r"<h3[^>]*>(.*?)</h3>", body, re.S | re.I)
            issue = re.search(r"Date of issue:\s*(\d{2})/(\d{2})/(\d{4})", body, re.I)
            if not title or not issue:
                raise ValueError(f"Missing NSO release title/date at {link}")
            day, month, year = issue.groups()
            issued = f"{year}-{month}-{day}"
            dates.append(issued)
            if issued >= start:
                rows.append({"title": clean(title.group(1)), "date": issued,
                             "url": html.unescape(link), "category": ARCHIVES[archive_slug],
                             "archive": archive_slug})
        if min(dates) < start or not re.search(r"[?&]paged=" + str(page + 1) + r"\b", html.unescape(raw)):
            break
        page += 1
    return rows


def article_text(url):
    raw = fetch(url).decode("utf-8", errors="replace")
    raw = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", raw, flags=re.I | re.S)
    return clean(raw)


def number(value):
    return float(value.replace(",", ""))


def period_from_title(title, cumulative=False):
    match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b.*?\b(20\d{2})\b", title, re.I)
    if not match:
        year = re.search(r"\b(20\d{2})\b", title)
        return year.group(1) if year else None
    month, year = match.group(1).title(), match.group(2)
    return f"January–{month} {year}" if cumulative else f"{month} {year}"


def report_period(title, text):
    half = re.search(r"first half of (20\d{2})", title + " " + text, re.I)
    if half:
        return f"January–June {half.group(1)}"
    months = re.search(r"(?:first\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+months? of (20\d{2})", title + " " + text, re.I)
    if months:
        value = months.group(1).lower()
        count = int(value) if value.isdigit() else {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}[value]
        month = next(name.title() for name, index in MONTHS.items() if index == count)
        return f"January–{month} {months.group(2)}"
    return period_from_title(title, cumulative=True)


def parse_metrics(item, text):
    """Return only observations found with a clear value and period."""
    archive_slug, title, url = item["archive"], item["title"], item["url"]
    metrics = {}
    period = report_period(title, text)
    if archive_slug == "monthly-report":
        fdi = re.search(r"disbursed FDI.{0,260}?(\d[\d,.]*)\s*billion\s*USD\s*\(?\+?\s*(-?\d+(?:\.\d+)?)\s*%\s*(?:YoY|year[- ]on[- ]year)", text, re.I | re.S)
        if fdi:
            metrics["fdi"] = {"value": number(fdi.group(1)), "yoy": number(fdi.group(2)), "period": period}

        retail = re.search(r"retail sales of goods and services.{0,400}?(?:eight|nine|seven|six|five|four|three|two|one|\d+) months.{0,180}?(\d[\d,.]*)\s*trillion\s*VND.{0,140}?(?:growth|increase|rise|up|shoot|expansion)\s*(?:of\s*)?(?:\+\s*)?(\d+(?:\.\d+)?)\s*%", text, re.I | re.S)
        if retail:
            metrics["retail_sales"] = {"value": number(retail.group(2)), "period": period}

        iip = re.search(r"Cumulatively,.{0,160}?IIP\s+(?:advanced|increased|grew|rose|expanded)\s+(?:by\s*)?(\d+(?:\.\d+)?)\s*%\s+over the corresponding period", text, re.I | re.S)
        if iip:
            metrics["industrial_production"] = {"value": number(iip.group(1)), "period": period}

        trade_change = re.search(r"exports and imports.{0,360}?(\d+(?:\.\d+)?)\s*%\s*(?:and|,).{0,60}?(\d+(?:\.\d+)?)\s*%", text, re.I | re.S)
        if trade_change:
            metrics.setdefault("exports", {})["yoy"] = number(trade_change.group(1))
            metrics.setdefault("imports", {})["yoy"] = number(trade_change.group(2))
            for key in ("exports", "imports"):
                metrics[key]["period"] = period

        export_value = re.search(r"Overall, the export turnover of goods in.{0,120}?(\d[\d,.]*)\s*billion\s*USD\s*\(\+?\s*\d+(?:\.\d+)?\s*%\s*YoY\)", text, re.I | re.S)
        import_value = re.search(r"Overall, the import turnover of goods in.{0,120}?(\d[\d,.]*)\s*billion\s*USD.{0,80}?(?:year-on-year|YoY)", text, re.I | re.S)
        if export_value:
            metrics.setdefault("exports", {})["value"] = number(export_value.group(1))
        if import_value:
            metrics.setdefault("imports", {})["value"] = number(import_value.group(1))
        for key in ("exports", "imports"):
            if key in metrics:
                metrics[key]["period"] = period

        gdp = re.search(r"(?:Gross Domestic Product \(GDP\)|GDP) in the second quarter of 20\d{2}.{0,180}?(?:rising|increased|grew|expanded) by (?:an estimated )?(\d+(?:\.\d+)?)\s*%", text, re.I | re.S)
        if gdp and re.search(r"quarter|Q[1-4]", title, re.I):
            metrics["gdp_growth"] = {"value": number(gdp.group(1)), "period": title}
        unemployment = re.search(r"unemployment rate.{0,180}?(\d+(?:\.\d+)?)\s*%", text, re.I | re.S)
        if unemployment and re.search(r"quarter|Q[1-4]|half", title, re.I):
            metrics["unemployment"] = {"value": number(unemployment.group(1)), "period": title}

    elif archive_slug == "cpi":
        cpi = re.search(r"CPI\).{0,240}?(\d+(?:\.\d+)?)\s*%\s*(?:year[- ]on[- ]year|compared with the same period of the previous year)", text, re.I | re.S)
        if cpi:
            period = period_from_title(title)
            parsed_period = re.search(r"(\w+)\s+(20\d{2})", period or "")
            unit = None
            if parsed_period and parsed_period.group(1).lower() in MONTHS:
                base_year = int(parsed_period.group(2)) - 1
                unit = f"index · {parsed_period.group(1)} {base_year} = 100"
            metrics["cpi"] = {"value": 100 + number(cpi.group(1)), "period": period, "unit": unit,
                               "basis": f"Rebased from NSO’s reported {number(cpi.group(1)):.2f}% year-on-year CPI change."}

    return metrics


def parse_trade_workbooks(release):
    """Read the official E01/E02 monthly total rows (thousand USD)."""
    from update_monthly_data import convert, release_links

    links, _ = release_links(release["url"])
    metrics = {}
    with tempfile.TemporaryDirectory(prefix="nso-headlines-") as temp:
        for url in links:
            match = re.search(r"E0([12])[-_]", urllib.parse.urlparse(url).path, re.I)
            if not match:
                continue
            metric = "exports" if match.group(1) == "1" else "imports"
            converted = convert(fetch(url), url, Path(temp) / metric)
            for sheet in converted:
                rows = sheet.get("rows_data", [])
                observation = parse_trade_sheet(metric, rows, release["title"])
                if observation:
                    metrics[metric] = observation
                    break
    return metrics


def parse_trade_sheet(metric, rows, fallback_title):
    title = " ".join(str(value) for row in rows[:3] for value in row if value not in (None, ""))
    expected = "export" if metric == "exports" else "import"
    if expected not in title.lower():
        return None
    total = next((row for row in rows if row and str(row[0]).strip().lower() == "total"), None)
    if not total:
        return None
    values = [value for value in total[1:] if str(value).strip()]
    if not values:
        return None
    latest = number(str(values[-1])) / 1_000_000
    month_names = []
    for row in rows[:5]:
        for value in row:
            if isinstance(value, str) and value.strip().lower() in MONTHS:
                month_names.append(value.strip().title())
    year_match = re.search(r"\b20\d{2}\b", title)
    period = f"January–{month_names[-1]} {year_match.group(0)} · preliminary" if month_names and year_match else period_from_title(fallback_title, cumulative=True)
    return {"value": latest, "period": period}


def apply(item, metric, observation, url):
    if "value" not in observation:
        return False
    before = json.dumps({key: item.get(key) for key in ("value", "yoy", "period", "source_url", "basis", "unit")}, sort_keys=True)
    item["value"] = observation["value"]
    item["source_url"] = url
    if observation.get("period"):
        item["period"] = observation["period"]
    if observation.get("yoy") is not None:
        item["yoy"] = observation["yoy"]
    if observation.get("basis"):
        item["basis"] = observation["basis"]
    if observation.get("unit"):
        item["unit"] = observation["unit"]
    item.pop("source_file", None)
    item.pop("source_value_thousand_usd", None)
    after = json.dumps({key: item.get(key) for key in ("value", "yoy", "period", "source_url", "basis", "unit")}, sort_keys=True)
    return before != after


def main():
    today = date.today()
    old = json.loads(HEADLINES.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in old["items"]}
    releases = []
    start = (today - timedelta(days=400)).isoformat()
    for archive_slug in ARCHIVES:
        releases.extend(archive(archive_slug, start))
    releases.sort(key=lambda row: (row["date"], row["url"]), reverse=True)

    # Check recent monthly reports for quarterly observations and current
    # economic indicators, then the most recent relevant dedicated releases.
    checks = []
    monthly = [row for row in releases if row["archive"] == "monthly-report"]
    checks.extend(monthly[:5])
    for archive_slug in ("cpi",):
        checks.extend([row for row in releases if row["archive"] == archive_slug][:1])
    checks = list({row["url"]: row for row in checks}.values())
    checks.sort(key=lambda row: (row["date"], row["url"]), reverse=True)

    changed = False
    parsed = set()
    seen_metrics = set()
    metric_dates = {}
    for release in checks:
        text = article_text(release["url"])
        for metric, observation in parse_metrics(release, text).items():
            if metric in seen_metrics:
                continue
            seen_metrics.add(metric)
            metric_dates[metric] = release["date"]
            item = by_id.get(metric)
            if item and apply(item, metric, observation, release["url"]):
                changed = True
                parsed.add(metric)

    trade_releases = [row for row in releases if row["archive"] == "import-export"]
    if trade_releases:
        trade = trade_releases[0]
        for metric, observation in parse_trade_workbooks(trade).items():
            if trade["date"] < metric_dates.get(metric, "0000-00-00"):
                continue
            item = by_id.get(metric)
            if item and apply(item, metric, observation, trade["url"]):
                changed = True
                parsed.add(metric)
                metric_dates[metric] = trade["date"]

    # An archive fetch and at least one full article fetch must succeed before
    # the checked date advances. This keeps the visible date meaningful.
    if not checks:
        raise RuntimeError("No NSO releases found in the daily lookback window")
    if changed:
        old["checked"] = today.isoformat()
        HEADLINES.write_text(json.dumps(old, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"changed={str(changed).lower()}\n")
    print(json.dumps({"checked": old["checked"], "articles_checked": len(checks),
                      "indicators_updated": sorted(parsed), "changed": changed}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Daily NSO headline check failed: {exc}", file=sys.stderr)
        raise
