# Vietnam provincial statistics for a public dashboard

Prepared from the previously downloaded NSO CSV collection. This is an independent data preparation project, not an official NSO product. No new downloads were required.

## Contents

- `observations.csv`: complete province-only dataset in long format.
- `by_section/`: the same observations split into the seven requested sections.
- `by_table/`: the same observations split by source table for loading on demand.
- `indicators.csv`: indicator names, breakdowns, units and default dashboard eligibility.
- `provinces.csv`: province names and project identifiers.
- `sources.csv`: original source URLs, titles, units, file locations and checksums.
- `sources/`: unchanged copies of the 91 source CSVs used in the dataset.
- `coverage.csv`: inclusion/exclusion result for every table examined in the seven source folders.
- `excluded_rows.csv`: aggregate and other non-province rows excluded from included tables.
- `quality_issues.csv`: source-title and definition issues.
- `data_dictionary.csv`: field definitions.
- `validation.json` and `package_validation.json`: validation results.

The master, section and table files contain alternate partitions of the SAME observations. Load one partitioning scheme; do not concatenate them together.

## Using the dataset

Join `observations.indicator_id` to `indicators.indicator_id`, and `source_id` to `sources.source_id`. Select an indicator, period and province to obtain a value. One indicator identifies a source table plus one breakdown, such as sex, school level, income quintile or land-use category. Labels preserve combined source categories rather than guessing how to split ambiguous text.

The unique observation key is `indicator_id + province_code + geography_version + period`. Different source tables can describe overlapping measures. Their IDs remain distinct; do not add these measures together. `Total` and its component categories must not be summed together either.

CSV encoding is UTF-8 with BOM. Values use a decimal point and have no thousands separators. Read province codes and periods as text. Values retain source units and scale: a value in thousand persons has NOT been multiplied by 1,000. Percentages remain percentage points, for example 22.6, not 0.226. A previous-year-equals-100 GRDP index remains an index, not a growth rate.

Missing source markers produce an empty `value`, with the original marker retained in `raw_value`. Zero remains zero. `period_status` retains preliminary, estimated and footnoted labels when present; `not_specified` does not mean final.

For a first dashboard, use records with a nonempty numeric value, a resolved period, and an indicator whose `default_dashboard_eligible` is `true`. This flag excludes known unresolved unit/definition problems; it is not a guarantee that all source methodological issues have been resolved. Surface source links and geography limitations in the UI.

## Geography

Only named provincial-level units are included. National totals, regional totals, military/central bodies, unspecified places and residual groups such as "Other provinces" are excluded. Weather, river and sea-level station observations are excluded even when station names match province names. Thus the administration/land/climate section supplies provincial administration and land data, not province-wide climate estimates.

`province_code` is a stable project identifier beginning `VN_SRC_`. It is NOT an official government administrative code. Spacing and punctuation variants of the same name are normalised, with the exact source name retained in `province_name_source`.

`geography_version = source_reported_unharmonized` explicitly means that the boundary vintage has not been established or harmonised. The collection includes historical names such as Ha Tay and both Hue and Thua Thien-Hue. These are retained as separate labels. The number of labels across the entire collection is not the number of simultaneous provinces.

Do not assume a 2025 observation uses the current 34-province map. Do not join this dataset to a map solely by name, automatically merge provinces, or compare long-term trends across boundary changes without checking the source definition. A verified geography crosswalk and chosen map vintage are a separate next step.

## Scope and source issues

The input scope is every downloaded table catalogued under these seven folders: population, employment, national_account, banking_insurance_budget, education, health_culture_environment, administration_land_climate. Other archive folders and historical spreadsheet attachments are outside this transformation, avoiding accidental mixing of different releases.

Banking/insurance/budget contributes three province-level insurance tables; national banking and budget aggregates are excluded. National accounts contributes the provincial GRDP index and GRDP per capita tables.

The title embedded in each CSV takes precedence over the website catalogue title. Both titles are retained in `sources.csv`; discrepancies are flagged. In particular, source IDs E0323/E0324/E0325 actually contain social/health/unemployment insurance respectively, and E1463 contains mobile-phone use.

E1322 and E1461 have unresolved apparent definition inconsistencies and are excluded from the default dashboard selection while retained in the complete dataset. No guessed corrections are made.

E1476 includes the malformed period label `Prel. 20204`. Those records retain that label, have no parsed year and use `period_type = unresolved_source_period`. They must be excluded from time charts until the intended year is confirmed. A period stated only in a table title, such as E1331 (2023), is explicitly identified by `period_basis` in the indicator catalogue.

Unit labels come from download metadata or explicit measure headings. No observations are aggregated, interpolated, seasonally adjusted or converted to new boundaries. Source methodology notes should be consulted before interpretation.

## GitHub upload plan

Use this folder as the data component of a public repository. The largest individual CSV is below GitHub's 100 MiB per-file limit. For the website, load only the required `by_table` files; the full master CSV is intended for analysis/download.

Upload the compressed dataset package and the original complete 45 MB archive as GitHub Release attachments. Do not place the entire working directory, raw download cache, credentials or audit working files in the repository. The data's NSO provenance is retained; this package does not assert an additional licence over the source data.

Uploading needs the destination repository URL (or owner and desired new repository name), the intended public visibility, and an authenticated GitHub session with write access on this computer. Do not send a password or access token in chat.
