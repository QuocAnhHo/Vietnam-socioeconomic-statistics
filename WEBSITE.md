# Website development

English-only React/Vite site, published from `main:/docs` on GitHub Pages. Hash routes preserve shared filters without server routing. `/explorer` and `/downloads` remain compatible aliases for `/dashboard` and `/publications`.

## Run, test and build

The prepared website data is committed. For ordinary UI development:

```sh
pnpm install
pnpm dev
pnpm test
python scripts/validate_downloads.py
pnpm build
```

Commit the rebuilt `docs/` output and push main. `.nojekyll` disables Jekyll processing. Node dependencies and local QA files are ignored. No backend, visitor account or database is required.

## Collections

Statistics preserves all 16,588 downloaded CSV files, grouped into 4,025 datasets. Individual source tables download as UTF-8 CSV; multi-sheet attachments download as ZIPs containing all CSV sheets. National and regional rows, all years, source markers and all series remain intact. Native tables are browsable in full. Attachment pages explicitly label their bounded first-sheet previews; downloads remain complete. `collection_manifest.json` maps every downloaded source file and checksum to its website dataset.

Dashboard contains 364 indicators and 283,619 observations across 13 provincial sections. A section filter scopes the indicator list. `public/webdata/series/` contains per-indicator JSON; `public/downloads/indicators/` contains corresponding complete CSV exports. Display filters do not restrict the primary download. Provinces are recognised only in tables with geographic fields or definitions, preventing non-geographic labels such as the fruit longan from matching Long An province. Units come from source metadata or explicit column definitions. Source issues remain flagged.

The original seven-section package in `data/` remains unchanged. To regenerate the expanded collection, extract the original archive into a sibling `NSO_CSV` directory, then run these steps in order:

```sh
python scripts/prepare_web_data.py
python scripts/expand_collection.py
python scripts/refine_dashboard_metadata.py
python scripts/prepare_indicator_downloads.py
python scripts/prepare_headlines.py
python scripts/prepare_statistics.py
```

For province-only regeneration, `expand_collection.py --dashboard-only` reuses the existing full catalogue. Always run `prepare_web_data.py` first to reset the baseline.

## Headline and publication snapshots

The homepage displays the latest verified national observations in `public/webdata/latest-headlines.json`. Population and GDP per capita use the latest annual national tables; GDP growth and unemployment use the latest quarterly release; the monthly indicators use the latest NSO release with a matching value. FDI, exports and imports include their year-on-year changes. A daily GitHub Actions check reads the English NSO release archives and their source pages/spreadsheets, and commits a new snapshot only when a parsed observation changes. A source value that cannot be confidently parsed is left at its last verified value.

`collect_publications.py` indexes the English NSO publication archive and the monthly-report, CPI, IIP and import-export archives, following pagination back to 29 September 2021. The index contains 40 publications and 186 statistical releases. `verify_publication_links.py` confirmed all 40 publication pages have downloadable file links. Files stay on NSO; visitors open the corresponding official detail page. Search, issue-year and type filters apply to the index. Re-running collection requires network access.

## Scheduled NSO data refresh

GitHub Actions runs two scheduled jobs. At 05:23 Vietnam time each day, the homepage job checks the monthly-report, CPI, industrial production and exports/imports sources and refreshes verified national headline observations when new values are available. At 06:23 on the first day of each month, the release-data job scans those same four Statistics sections and converts newly linked Excel/CSV/ZIP spreadsheet attachments sheet-by-sheet to UTF-8 CSV, adding them to release detail pages and complete downloads in the rolling five-year index. Both jobs support manual runs from the repository Actions tab. PDF attachments and report prose are not extracted into the downloadable datasets.

The workflows rebuild and push GitHub Pages files only when the headline values or release index/data change. A page-format or download error fails the run without publishing partial results; the failed run is visible in GitHub Actions. Spreadsheet conversion requires the packages listed in `scripts/requirements-monthly-update.txt`. The jobs are `scripts/update_latest_headlines.py` (daily) and `scripts/update_monthly_data.py` (monthly).

## Geography and privacy

See `map_sources/README.md`. The map is a 2020, 63-province historical reference used for annual periods 2009–2024 only. Other periods remain available in tables and downloads. Source geography is not harmonised; never infer the current 34 provinces or sum rates. Comparison charts support up to five provinces. Census remains a placeholder. The website collects no user data; shareable links contain only statistical filters.

## Statistics navigation and release data (30 September 2026)

Stage 1 was deployed as commit ef673ef before collecting the four release categories. Statistics uses the four NSO subject groups, compact original-title rows and eight shortcut blocks. The NSDP and historical catch-all topics are hidden; original downloadable data remains intact. The visible 810 subject datasets have chart and metadata views: 599 have automatically prepared time series (46,438 series), with source-column chart controls for irregular or cross-sectional layouts. Every automatic chart value is checked against its original source cell; no source geography is removed. Downloads are never restricted by chart selections.

`scripts/collect_release_data.py` matches spreadsheet URLs to the existing attachment inventory before downloading missing files. It reviewed 184 releases dated 30 September 2021–30 September 2026: 59 monthly reports, 59 CPI releases, 60 IIP releases and six annual exports/imports release pages. It reused all 215 linked spreadsheet attachments, with no repeat downloads. 179 releases contain 1,954 data sheets; five releases are PDF-only and remain official-page links. Each release and each category offers a complete CSV ZIP, including a source manifest. The four category ZIPs contain 1,585 monthly-report, 268 CPI, 59 IIP and 42 trade sheets. No PDF or narrative report data is extracted.

Release records live in `public/webdata/release-details/`; the category index is `release-catalogue.json`. Run `python scripts/validate_releases.py` to compare every downloaded sheet with the saved original CSV and validate ZIP integrity. Downloaded source files and review caches stay outside the published data paths. Recollection needs the sibling original NSO_CSV archive and attachment inventory; normal website builds use the committed prepared data.

## Statistics navigation (1 October 2026)

The Statistics landing page follows the ABS category-and-card presentation using NSO's subject structure. Four subject sections contain 13 topic cards, followed by four release sections. A shared sticky sidebar has no dataset counts, separate category links and subsection toggles, and scroll-driven active-category highlighting on the landing page. Topic lists, source dataset pages and release detail pages retain the same sidebar and selected subsection. On phones the sidebar collapses behind Browse statistics. Topic and search links remain shareable hash routes; complete data downloads are unchanged.
