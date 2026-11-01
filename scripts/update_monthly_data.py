"""Refresh the four selected NSO release sections from the English archives.

This script is self-contained so it can run from GitHub Actions. It fetches only
spreadsheet attachments linked by release pages; PDFs and report prose are not
converted into data.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import csv
import datetime
import hashlib
import html
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import zipfile

from openpyxl import load_workbook
import xlrd
from python_calamine import CalamineWorkbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public"
WEB = OUT / "webdata"
DATA = ROOT / "data" / "release_csv"
ARCHIVES = {
    "monthly-report": "Socio-economic reports",
    "cpi": "CPI, gold & USD indexes",
    "iip": "Index of Industrial Production",
    "import-export": "Preliminary Exports and Imports",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VietnamStatisticsExplorer/1.0)"}


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


def slug(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")[:80] or "sheet"


def csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        if isinstance(value, datetime.datetime):
            return value.isoformat(sep=" ")
        return value.isoformat()
    return value


def archive(archive_slug, start):
    rows = []
    page = 1
    while page <= 30:
        url = f"https://www.nso.gov.vn/en/{archive_slug}/" + (f"?paged={page}" if page > 1 else "")
        text = fetch(url).decode("utf-8", errors="replace")
        entries = re.findall(
            r'<a\s+href=["\']([^"\']+)["\'][^>]*>\s*(?:</p>\s*)?<section class="item">(.*?)</section>',
            text,
            re.S | re.I,
        )
        if not entries:
            raise ValueError(f"NSO archive format changed or returned no entries: {url}")
        dates = []
        for link, body in entries:
            title = re.search(r"<h3[^>]*>(.*?)</h3>", body, re.S | re.I)
            date = re.search(r"Date of issue:\s*(\d{2})/(\d{2})/(\d{4})", body, re.I)
            if not title or not date:
                raise ValueError(f"Missing NSO release title/date at {link}")
            day, month, year = date.groups()
            issued = f"{year}-{month}-{day}"
            dates.append(issued)
            if issued >= start:
                rows.append({"title": clean(title.group(1)), "date": issued, "url": html.unescape(link),
                             "category": ARCHIVES[archive_slug], "archive": archive_slug})
        if min(dates) < start or not re.search(r"[?&]paged=" + str(page + 1) + r"\b", html.unescape(text)):
            break
        page += 1
    return rows


def release_links(url):
    text = fetch(url).decode("utf-8", errors="replace")
    attrs = re.findall(r"(?:href|src)=[\"']([^\"']+)[\"']", text, re.I)
    urls = list(dict.fromkeys(urllib.parse.urljoin(url, html.unescape(link)) for link in attrs))
    spreadsheets = [u for u in urls
                    if re.search(r"\.(?:xlsx?|csv|zip)(?:[?#]|$)", u, re.I)
                    and urllib.parse.urlparse(u).hostname in ("www.nso.gov.vn", "nso.gov.vn")]
    pdfs = sum(bool(re.search(r"\.pdf(?:[?#]|$)", u, re.I)) for u in urls)
    return spreadsheets, pdfs


def write_csv(rows, destination):
    while rows and not any(value not in (None, "") for value in rows[-1]):
        rows.pop()
    width = max((len(row) for row in rows), default=0)
    if not width:
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized = [[csv_value(value) for value in row] + [""] * max(0, width - len(row)) for row in rows]
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream).writerows(normalized)
    with destination.open(encoding="utf-8-sig", newline="") as stream:
        check = list(csv.reader(stream))
    if len(check) != len(normalized) or any(len(row) != width for row in check):
        raise ValueError(f"CSV verification failed: {destination}")
    return {"path": destination.relative_to(ROOT).as_posix(), "rows": len(normalized), "columns": width,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}


def convert(blob, filename, folder):
    extension = Path(urllib.parse.urlparse(filename).path).suffix.lower()
    result = []
    if blob.startswith(b"PK") and extension == ".zip":
        with zipfile.ZipFile(io.BytesIO(blob)) as archive_file:
            for name in archive_file.namelist():
                if name.startswith("__MACOSX/") or name.endswith("/"):
                    continue
                if Path(name).suffix.lower() in (".xlsx", ".xls", ".csv", ".zip"):
                    result.extend(convert(archive_file.read(name), name, folder / slug(Path(name).stem)))
        return result
    if extension == ".csv":
        try:
            text = blob.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = blob.decode("cp1258")
        rows = list(csv.reader(io.StringIO(text)))
        meta = write_csv(rows, folder / "data.csv")
        return [{**meta, "sheet": "data", "rows_data": rows}] if meta else []
    if blob.startswith(b"PK"):
        workbook = load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
        try:
            for index, sheet in enumerate(workbook.worksheets):
                rows = [list(row) for row in sheet.iter_rows(values_only=True)]
                meta = write_csv(rows, folder / f"{index + 1:03d}_{slug(sheet.title)}.csv")
                if meta:
                    result.append({**meta, "sheet": sheet.title,
                                   "rows_data": [[csv_value(value) for value in row] for row in rows]})
        finally:
            workbook.close()
        return result
    if blob.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        try:
            workbook = xlrd.open_workbook(file_contents=blob, logfile=io.StringIO())
            for index, sheet in enumerate(workbook.sheets()):
                rows = []
                for row_index in range(sheet.nrows):
                    row = []
                    for cell in sheet.row(row_index):
                        value = cell.value
                        if cell.ctype == xlrd.XL_CELL_DATE:
                            try:
                                value = xlrd.xldate_as_datetime(value, workbook.datemode)
                            except ValueError:
                                pass
                        elif cell.ctype == xlrd.XL_CELL_ERROR:
                            value = xlrd.error_text_from_code.get(value, str(value))
                        row.append(value)
                    rows.append(row)
                meta = write_csv(rows, folder / f"{index + 1:03d}_{slug(sheet.name)}.csv")
                if meta:
                    result.append({**meta, "sheet": sheet.name,
                                   "rows_data": [[csv_value(value) for value in row] for row in rows]})
            return result
        except Exception:
            workbook = CalamineWorkbook.from_filelike(io.BytesIO(blob))
            for index, name in enumerate(workbook.sheet_names):
                rows = workbook.get_sheet_by_index(index).to_python(skip_empty_area=False)
                meta = write_csv(rows, folder / f"{index + 1:03d}_{slug(name)}.csv")
                if meta:
                    result.append({**meta, "sheet": name,
                                   "rows_data": [[csv_value(value) for value in row] for row in rows]})
            return result
    raise ValueError(f"Not a supported spreadsheet: {filename}")


def make_detail(item):
    release_id = item["archive"] + "-" + hashlib.sha256(item["url"].encode()).hexdigest()[:12]
    links, pdf_count = release_links(item["url"])
    detail = {**item, "id": release_id, "attachments": [], "errors": [], "sheets": [], "series": [],
              "reason": "The release spreadsheets retain their original headings. Select a sheet and columns to chart the source observations.",
              "spreadsheet_links": links, "pdf_links": pdf_count}
    for attachment_index, url in enumerate(links):
        blob = fetch(url)
        digest = hashlib.sha256(blob).hexdigest()
        folder = DATA / release_id / f"{attachment_index + 1:02d}-{slug(Path(urllib.parse.urlparse(url).path).stem)}"
        converted = convert(blob, url, folder)
        if not converted:
            raise ValueError(f"No readable spreadsheet sheets at {url}")
        files = []
        for sheet_index, sheet in enumerate(converted):
            archive_name = f"{attachment_index + 1:02d}-{sheet_index + 1:03d}-{Path(sheet['path']).name}"
            detail["sheets"].append({"name": Path(urllib.parse.urlparse(url).path).name + " · " + sheet["sheet"],
                                     "rows": sheet["rows_data"], "archive_name": archive_name, "source_url": url})
            files.append({key: value for key, value in sheet.items() if key != "rows_data"})
        detail["attachments"].append({"url": url, "action": "downloaded", "sha256": digest, "files": files})
    detail["download"] = f"downloads/releases/{release_id}.zip" if detail["sheets"] else None
    detail["chart_file"] = f"release-details/{release_id}.json"
    detail["source_id"] = release_id
    detail["source_url"] = item["url"]
    detail["coverage_note"] = "No spreadsheet attachment is linked from this release page." if not detail["sheets"] else "All sheets from linked spreadsheet attachments are included."
    return detail


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    csv.writer(stream).writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def write_release_zip(detail, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = [["file", "source_url", "release_url", "issue_date"]]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive_file:
        for sheet in detail["sheets"]:
            archive_file.writestr(sheet["archive_name"], csv_bytes(sheet["rows"]))
            manifest.append([sheet["archive_name"], sheet["source_url"], detail["url"], detail["date"]])
        archive_file.writestr("sources.csv", csv_bytes(manifest))


def five_year_start(today):
    try:
        return today.replace(year=today.year - 5)
    except ValueError:
        return today.replace(year=today.year - 5, day=28)


def set_action_output(name, value):
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"{name}={str(value).lower()}\n")


def main():
    today = datetime.date.today()
    start = five_year_start(today).isoformat()
    found = []
    for archive_slug in ARCHIVES:
        found.extend(archive(archive_slug, start))
    found = list({item["url"]: item for item in found}.values())
    found.sort(key=lambda item: (item["date"], item["url"]), reverse=True)

    publications_path = WEB / "publications.json"
    publications = json.loads(publications_path.read_text(encoding="utf-8"))
    publication_items = [item for item in publications["items"]
                         if item.get("archive") not in ARCHIVES or item["date"] >= start]
    known_urls = {item["url"] for item in publication_items}
    publication_items.extend(item for item in found if item["url"] not in known_urls)
    publication_items.sort(key=lambda item: (item["date"], item["url"]), reverse=True)

    catalogue_path = WEB / "release-catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    release_items = [item for item in catalogue["items"]
                     if item.get("archive") not in ARCHIVES or item["date"] >= start]
    known_ids = {item["id"] for item in release_items}
    new_items = [item for item in found if item["archive"] + "-" + hashlib.sha256(item["url"].encode()).hexdigest()[:12] not in known_ids]
    print(f"Scanned NSO archives: {len(found)} releases in five years; {len(new_items)} are new.", flush=True)

    details = []
    if new_items:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(make_detail, item) for item in new_items]
            for future in as_completed(futures):
                details.append(future.result())
    new_by_id = {detail["id"]: detail for detail in details}
    for detail in details:
        write_json(WEB / detail["chart_file"], detail)
        write_release_zip(detail, OUT / detail["download"])
        release_items.append({key: detail[key] for key in
                              ("id", "title", "date", "url", "archive", "download", "chart_file", "coverage_note")}
                             | {"sheets": len(detail["sheets"]), "errors": len(detail["errors"])})
    release_items.sort(key=lambda item: (item["date"], item["url"]), reverse=True)
    changed = bool(details) or publication_items != publications["items"] or release_items != catalogue["items"]
    if not changed:
        print("No new release pages or downloads; site data is unchanged.")
        set_action_output("changed", False)
        return
    set_action_output("changed", True)

    packages = []
    for archive_slug in ARCHIVES:
        grouped = [item for item in release_items if item["archive"] == archive_slug]
        old_package = next((package for package in catalogue.get("packages", [])
                            if package["archive"] == archive_slug), None)
        if archive_slug in ARCHIVES:
            package_path = f"downloads/releases/{archive_slug}-latest-five-years.zip"
            target = OUT / package_path
            target.parent.mkdir(parents=True, exist_ok=True)
            manifest = [["file", "release_url", "issue_date", "spreadsheet_url"]]
            sheets_count = 0
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive_file:
                for item in grouped:
                    detail = new_by_id.get(item["id"])
                    if detail is None:
                        detail = json.loads((WEB / item["chart_file"]).read_text(encoding="utf-8"))
                    for sheet in detail["sheets"]:
                        name = f"{item['date']}-{item['id']}/{sheet['archive_name']}"
                        archive_file.writestr(name, csv_bytes(sheet["rows"]))
                        manifest.append([name, item["url"], item["date"], sheet["source_url"]])
                        sheets_count += 1
                archive_file.writestr("sources.csv", csv_bytes(manifest))
            packages.append({"archive": archive_slug, "download": package_path,
                             "releases": len(grouped), "sheets": sheets_count})
        elif old_package:
            packages.append(old_package)

    publications.update({"items": publication_items, "from": start, "to": today.isoformat(), "checked": today.isoformat()})
    catalogue.update({"items": release_items, "from": start, "to": today.isoformat(),
                      "checked": today.isoformat(), "packages": packages})
    write_json(publications_path, publications)
    write_json(catalogue_path, catalogue)
    print(json.dumps({"new_releases": len(details), "new_sheets": sum(len(detail["sheets"]) for detail in details),
                      "release_index_entries": len(release_items), "publication_entries": len(publication_items)}), flush=True)


if __name__ == "__main__":
    main()
