# Live Data Portal — Energy Transport & Commodity Prices

A fully automated pipeline: public data sources → ingest → transform →
static dashboard, refreshed on a schedule with no server to run or database
to manage. v1 covers two subjects:

- **Commodity prices**: WTI, Brent, Henry Hub, EU natural gas, US gasoline/diesel.
- **Energy trade flows**: crude oil exports/imports by country.

## How it works

```
ingestion/*.py   -> pulls raw data from each source, writes data/raw/<source>/<date>.json
transform/*.py   -> aggregates raw snapshots into docs/data/processed/*.json
docs/            -> static dashboard (plain HTML/CSS/JS + Chart.js) that reads that JSON
.github/workflows/pipeline.yml -> runs the above every 6 hours, commits the result
```

It's "git as database": there's no backend and no database server. GitHub
Actions runs the scripts on a schedule, commits the refreshed JSON straight
into the repo, and GitHub Pages redeploys the `docs/` folder automatically.

### Data sources (all free)

| Source | Data | Key needed |
|---|---|---|
| [FRED](https://fred.stlouisfed.org/) | Benchmark prices: WTI, Brent, Henry Hub, EU gas | `FRED_API_KEY` |
| [EIA](https://www.eia.gov/opendata/) | US retail gasoline & diesel prices | `EIA_API_KEY` |
| [JODI-Oil](https://www.jodidata.org/oil/) | Crude oil exports/imports by country | none |
| [UN Comtrade](https://comtradeplus.un.org/) | Bilateral crude oil trade (optional, adds country-pair detail on top of JODI) | `COMTRADE_API_KEY` (optional) |

Adding a new subject later means: add one `ingestion/<source>.py` script, one
entry in `config/series.yaml`, and one `transform/build_<thing>.py` — the
rest of the pipeline (scheduling, commit, deploy) doesn't change.

## One-time setup (you need to do this — I can't create accounts on your behalf)

1. **Get free API keys:**
   - FRED: <https://fred.stlouisfed.org/docs/api/api_key.html>
   - EIA: <https://www.eia.gov/opendata/register.php>
   - (Optional) UN Comtrade: <https://comtradedeveloper.un.org/> — skip this and the pipeline still runs fine on FRED/EIA/JODI alone.

2. **Create a GitHub repository** and push this project to it:
   ```bash
   git remote add origin https://github.com/<you>/<repo>.git
   git branch -M main
   git push -u origin main
   ```

3. **Add repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `FRED_API_KEY`
   - `EIA_API_KEY`
   - `COMTRADE_API_KEY` (optional)

4. **Enable GitHub Pages**: Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder: `/docs`. Save.

5. **Trigger the first run**: Actions tab → "Data pipeline" → "Run workflow". After it completes, your site (URL shown at Settings → Pages) will show live data. It then keeps refreshing itself every 6 hours automatically — no further action needed.

## Running locally

```bash
pip install -r requirements.txt

export FRED_API_KEY=...      # or $env:FRED_API_KEY = "..." on PowerShell
export EIA_API_KEY=...
# COMTRADE_API_KEY optional

cd ingestion
python fred.py
python eia.py
python jodi.py       # no key needed
python comtrade.py   # skips cleanly if COMTRADE_API_KEY unset

cd ../transform
python build_prices.py
python build_flows.py
python build_meta.py

cd ../docs
python -m http.server 8000
# open http://localhost:8000
```

## Extending to a new subject

1. Add a source config block to `config/series.yaml`.
2. Add `ingestion/<source>.py` (use `ingestion/common.py`'s `fetch_json` /
   `fetch_text` / `write_raw_snapshot` helpers — same pattern as the existing
   scripts).
3. Add `transform/build_<thing>.py` that reads the raw snapshot and writes a
   frontend-ready JSON file into `docs/data/processed/`.
4. Add a new section to `docs/index.html` + rendering logic in
   `docs/dashboard.js` that fetches and displays it.
5. Add the new ingestion/transform scripts to
   `.github/workflows/pipeline.yml`'s run steps.

## Notes on data freshness

Prices update daily/weekly; trade flow data (JODI) updates monthly with
about a one-month lag — this is a real constraint of the free public data,
not a bug. The dashboard footer shows each source's actual last-updated
date rather than implying everything is equally live.
