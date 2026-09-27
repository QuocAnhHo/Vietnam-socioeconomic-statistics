# Vietnam socio-economic statistics

Province-level statistics prepared from public CSV data published by Vietnam's National Statistics Office (NSO), for an independent personal website and dashboard project.

**161,709 observations · 231 indicator series · 91 source tables**

[Visit the website](https://quocanhho.github.io/Vietnam-socio-economics-statistics/) · [Open the population explorer](https://quocanhho.github.io/Vietnam-socio-economics-statistics/#/explorer)

The English-language website includes a searchable statistics catalogue, dataset pages, downloads and a population explorer with 32 indicators, historical province maps, rankings, trends, comparisons and CSV exports. Census is a coming-soon placeholder. This is an independent personal project, not an official NSO website, and does not imply government endorsement.

See [WEBSITE.md](WEBSITE.md) for local development, rebuilding and GitHub Pages deployment.

## Download and explore

- [Combined province dataset](data/observations.csv)
- [Data by section](data/by_section/)
- [Data by source table](data/by_table/) — suitable for loading on demand in a website
- [Indicator catalogue](data/indicators.csv)
- [Province identifiers](data/provinces.csv)
- [Sources and provenance](data/sources.csv)
- [Data dictionary](data/data_dictionary.csv)
- [Full data guide](data/README.md)
- [Downloadable archives](https://github.com/QuocAnhHo/Vietnam-socio-economics-statistics/releases)

The complete CSV archive contains 16,588 original/converted CSV files across the wider NSO collection. The separate province dashboard package contains the prepared data in this repository. Both are intended to be available as release attachments.

## Coverage

| Section | Indicator series | Observations |
|---|---:|---:|
| Population | 32 | 34,329 |
| Employment | 7 | 4,934 |
| National accounts | 2 | 1,008 |
| Banking, insurance and budget | 3 | 1,890 |
| Education | 57 | 53,312 |
| Health, culture and environment | 109 | 55,022 |
| Administration, land and climate | 21 | 11,214 |

The scope is provincial observations from the seven selected source folders. National and regional aggregates are excluded. The banking section contributes provincial insurance statistics; weather-station data is excluded because it does not represent whole provinces.

## Data format

Each row is a province, indicator/breakdown and period. Core columns are `section`, `indicator_id`, `province_code`, `province_name`, `geography_version`, `period`, `year`, `value`, `unit` and `source_id`. Additional columns preserve missing-value status, preliminary/estimated labels and original source coordinates.

Join `indicator_id` to `data/indicators.csv` and `source_id` to `data/sources.csv`. CSVs use UTF-8 with BOM. Empty values represent missing data, not zero. Units and scales are preserved.

The master file and files under `by_section` and `by_table` are alternative partitions of the same data. Do not concatenate all three together.

## Geography and quality

- Province identifiers beginning `VN_SRC_` are project IDs, not official administrative codes.
- Historical names remain separate, including Ha Tay, Hue and Thua Thien-Hue. Boundaries have not been harmonised. A 2025 label must not be assumed to refer to the current 34-province map.
- Two source definitions need review. The indicator catalogue excludes them from the default dashboard selection.
- 315 observations retain a malformed source year and must be excluded from time charts until confirmed.
- Values were checked against their source cells. [Validation](data/package_validation.json) also covers unique observation keys, source checksums and partition counts.

## Attribution

Source: [National Statistics Office of Vietnam](https://www.nso.gov.vn/en/homepage/). Individual table URLs and checksums are retained in the source catalogue. The source snapshot was collected in September 2026; the province package was prepared on 28 September 2026.

No additional licence over NSO source data is asserted by this project. Consult the original source terms before reuse.
