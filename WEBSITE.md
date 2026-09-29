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
```

For province-only regeneration, `expand_collection.py --dashboard-only` reuses the existing full catalogue. Always run `prepare_web_data.py` first to reset the baseline.

## Headline and publication snapshots

Headlines were checked on 29 September 2026. Population and GDP per capita use 2025 national tables; GDP growth uses Q2 2026; disbursed FDI and trade use January–August 2026. Trade uses the September 19 preliminary release. CPI explicitly rebases the reported annual change to August 2025 = 100; both annual and monthly changes are shown. Every card includes its period, unit, basis and official source. This is a dated snapshot, not an automatic live feed.

`collect_publications.py` indexes the English NSO publication archive and the monthly-report, CPI, IIP and import-export archives, following pagination back to 29 September 2021. The index contains 40 publications and 186 statistical releases. `verify_publication_links.py` confirmed all 40 publication pages have downloadable file links. Files stay on NSO; visitors open the corresponding official detail page. Search, issue-year and type filters apply to the index. Re-running collection requires network access.

## Geography and privacy

See `map_sources/README.md`. The map is a 2020, 63-province historical reference used for annual periods 2009–2024 only. Other periods remain available in tables and downloads. Source geography is not harmonised; never infer the current 34 provinces or sum rates. Comparison charts support up to five provinces. Census remains a placeholder. The website collects no user data; shareable links contain only statistical filters.
