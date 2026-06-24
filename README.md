# Stock Screener

A Streamlit app that lets you find stocks using plain English. Type a query like *"show me tech stocks with a market cap over 1 billion and a beta less than 1.5"* and get a formatted summary of matching companies plus their latest SEC 8-K filings.

## How it works

1. Your query is sent to **GPT-4o-mini** which extracts filter parameters and calls the FMP stock screener API
2. The app fetches **SEC 8-K filings** for each result from the FMP filings API
3. **GPT-4o** streams a human-readable summary back to you

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

**3. Add your API keys**

Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

- [OpenAI API key](https://platform.openai.com/api-keys)
- [Financial Modeling Prep API key](https://financialmodelingprep.com/developer/docs)

**4. Run the app**
```bash
streamlit run app.py
```

## Example queries

- `show me healthcare stocks with a dividend greater than 2`
- `find NASDAQ tech stocks with a market cap over 10 billion and beta less than 1`
- `show me actively trading energy stocks priced under $50`
