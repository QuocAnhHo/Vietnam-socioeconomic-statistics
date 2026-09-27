# Website development

English-only React/Vite website. Routes use URL hashes so shared views work on GitHub Pages without server-side routing.

## Run locally

```sh
pnpm install
python scripts/prepare_web_data.py
pnpm dev
```

## Test and build

```sh
pnpm test
pnpm build
```

The production output goes into `docs/`. GitHub Pages publishes the main branch's `/docs` folder. A `.nojekyll` file in public assets disables Jekyll processing. Commit the updated production output after building.

## Data flow

`data/observations.csv` and catalogues are the authoritative prepared statistical inputs. `scripts/prepare_web_data.py` produces compact, per-indicator JSON files under `public/webdata/`. Each view loads its requested series on demand. Source data files and the complete collection stay accessible from the repository and Release attachments.

No backend, database or account is required for visitors. The site does not collect user data. Shareable URLs contain only the chosen statistical filters.

The population explorer has 32 source series, a historical reference map, year and province selection, rankings, up to five comparison provinces, accessible table alternatives, CSV downloads and source links. The Census page is deliberately a placeholder. Other topics have dataset pages and table downloads.

## Geometry

See `map_sources/README.md`. All 63 map names are checked against project identifiers during preparation. The source statistical geography remains unharmonised. Never infer a 34-province geography from this dataset or automatically sum rates.

## Deployment

Build locally and commit `docs/`, then push main. Pages is configured to serve `/docs`. Node dependencies and local QA artifacts are ignored. Credentials are never part of this repository.
