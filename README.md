# Stock Screener

A Streamlit app that lets you find stocks using plain English. Type a query like *"show me tech stocks with a market cap over 1 billion and a beta less than 1.5"* and get a formatted summary of matching companies plus their latest SEC 8-K filings.

## How it works

1. Your query is sent to **GPT-4o-mini** which extracts filter parameters and calls the stock screener
2. **yfinance** screens stocks from Yahoo Finance — no API key needed, completely free
3. The app fetches recent **SEC 8-K filings** for each result via Yahoo Finance
4. **GPT-4o** streams a human-readable summary back to you

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/elenajdata/stock-picker-streamlit.git
cd stock-picker-streamlit
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your OpenAI API key**

Copy `.env.example` to `.env` and fill in your key:
```bash
cp .env.example .env
```

Get your key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

> Stock data is sourced from Yahoo Finance via `yfinance` — no additional API key required.

**4. Run the app**
```bash
python -m streamlit run app.py
```
> **Windows note:** `streamlit` may not be on your PATH. Using `python -m streamlit` avoids that issue entirely.
> This app was built and tested on **Python 3.14**. Python 3.10+ is recommended.

## Example queries

- `show me tech stocks with a market cap over 1 billion and a beta less than 1.5`
- `find healthcare stocks with a dividend yield greater than 2%`
- `show me energy stocks priced under $50`
- `give me large cap financial stocks with volume greater than 1 million`
- `show me consumer discretionary stocks on the NYSE`
