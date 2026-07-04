# Datawash — Data Cleaner & Analyzer

Upload a messy CSV or Excel file, get an automatic data quality report, clean it with one-click recommendations, explore it with real statistical charts, build a custom dashboard, and export everything — including embedded chart images — as one Excel report.

**Live demo:** _add your deployed Streamlit Cloud link here once deployed_

---

## What it does

Datawash walks any messy dataset through 6 stages:

1. **Upload** — reads CSV or Excel, with file-size and format validation
2. **Diagnose** — automatically detects missing values, duplicate rows, statistical outliers (IQR method), currency-formatted columns, and inconsistent text formatting
3. **Clean** — threshold-based recommendations for dropping mostly-empty columns/rows, mean/median/mode filling, currency conversion, text standardization — every fix requires explicit confirmation, nothing is auto-applied
4. **Explore** — summary statistics, histograms, categorical breakdowns, time trends, grouped comparisons, scatter plots, and box plots
5. **Dashboard** — pick any chart or insight from Explore and add it to a custom dashboard
6. **Export** — download a single Excel workbook containing the cleaned data, summary statistics, insights, and your dashboard charts embedded as images

---

## Tech stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web app framework / UI |
| pandas | Data manipulation |
| Plotly | Interactive charts |
| Kaleido | Renders charts to static images for export |
| openpyxl | Builds the Excel export, embeds chart images |
| Pillow | Image handling |

---

## Running it locally

**1. Clone or download this repository**
```bash
git clone <your-repo-url>
cd datawash
```

**2. Install dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```
(Drop `--break-system-packages` if you're using a virtual environment, which is recommended.)

**3. Run the app**
```bash
streamlit run app.py
```

**4. Open in browser**
It should open automatically at `http://localhost:8501`. If not, open that URL manually.

**5. Try it immediately**
Upload the included `sample_messy_sales_data.csv` — it has missing values, duplicates, inconsistent text casing, currency-formatted numbers, and outliers already baked in, so every feature has something to show right away.

---

## Project structure

```
datawash/
├── app.py                        # Main app — all 6 pipeline stages
├── requirements.txt
├── sample_messy_sales_data.csv   # Test file with intentional data issues
├── .streamlit/
│   └── config.toml               # Theme colors
└── modules/
    ├── data_loader.py            # File reading + validation
    ├── type_detector.py          # Auto column-type detection
    ├── quality_check.py          # Missing values, duplicates, outliers, drop recommendations
    ├── cleaner.py                # Cleaning operations (fill, drop, standardize)
    ├── eda.py                    # Summary statistics, grouped comparison, skewness
    ├── visualizer.py             # 7 chart types
    ├── dashboard.py              # Rebuilds saved chart configs on demand
    └── export.py                 # Excel export with embedded chart images
```

Each module has a single, focused responsibility, so functions can be tested and understood independently of the UI.

---

## Deploying your own copy (free)

1. Push this repo to your own GitHub account (public)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app**, select your repo, set main file to `app.py`
4. Deploy — you'll get a live URL in a couple of minutes

---

## Known limitations

- No automated test suite is included in this repo (testing was done via manual and scripted verification during development)
- Single-session tool — no user accounts, authentication, or persistent storage between sessions
- Very large files (100,000+ rows) aren't explicitly chunked; a 200MB upload limit is enforced as a safety guard
- Kaleido is pinned to version `0.2.1` specifically because newer versions require a separate Chrome installation to render chart images — this version bundles its own renderer instead

---

## License

Feel free to use, modify, and learn from this project.
