# Mamaearth Growth Analytics

## Project Overview
This project analyzes a synthetic educational e-commerce dataset inspired by Mamaearth. It covers SQL reporting, Python data cleaning and exploratory analysis, visualization, and AI-assisted business narrative generation.

**Important:** The dataset is synthetic. Findings must not be interpreted as official Mamaearth business performance.

## Project Structure
- `sql/` — database schema, seed data, and analytical reports
- `data/` — source CSV files
- `analysis/` — data cleaning, exploratory analysis, and visualization scripts
- `visualizations/` — generated charts
- `narrator/` — computed findings, narrative-generation script, and sample output
- `run_seed.py` — initializes and seeds the SQLite database
- `run_reports.py` — runs SQL reports

## Requirements
- Python 3
- Packages listed in `requirements.txt`
- A Gemini API key for online narrative generation (optional; offline fallback is available)

## Setup
Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Order
Run these commands from the project root:

```bash
python run_seed.py
python run_reports.py
python analysis/clean_and_eda.py
python analysis/visualize.py
python analysis/create_findings.py
python narrator/generate_narrative.py
```

## Gemini API
Set `GEMINI_API_KEY` as an environment variable before running the narrative generator if you want to use Gemini. Do not put the key in source code or commit it to GitHub.

The generator uses a 30-second timeout and falls back to a deterministic offline narrative if the API request fails or the generated output fails the accuracy check.

## Key Findings
- 180 raw orders were supplied.
- 5 duplicate submissions were removed, leaving 175 orders.
- Cleaned revenue was ₹236,109.75.
- COD had the highest observed return rate at 35.38% across 65 orders.
- The peak revenue month differs when flagged quantity outliers are excluded.

## Limitations
This analysis uses synthetic educational data. Observed relationships are descriptive and do not establish causation.