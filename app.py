import streamlit as st
from openai import OpenAI
import yfinance as yf
from yfinance.screener import screen, EquityQuery
import json
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("Stock Screener")
st.write("Ask in plain English — get a summary of matching stocks and their latest SEC filings.")


def stock_screener(market_cap_more_than=None, market_cap_less_than=None,
                   price_more_than=None, price_less_than=None,
                   beta_more_than=None, beta_less_than=None,
                   volume_more_than=None, volume_less_than=None,
                   dividend_yield_more_than=None,
                   sector=None, industry=None, exchange=None, limit=10):

    filters = []

    if market_cap_more_than:
        filters.append(EquityQuery('gt', ['intradaymarketcap', market_cap_more_than]))
    if market_cap_less_than:
        filters.append(EquityQuery('lt', ['intradaymarketcap', market_cap_less_than]))
    if price_more_than:
        filters.append(EquityQuery('gt', ['intradayprice', price_more_than]))
    if price_less_than:
        filters.append(EquityQuery('lt', ['intradayprice', price_less_than]))
    if beta_more_than:
        filters.append(EquityQuery('gt', ['beta', beta_more_than]))
    if beta_less_than:
        filters.append(EquityQuery('lt', ['beta', beta_less_than]))
    if volume_more_than:
        filters.append(EquityQuery('gt', ['avgdailyvol3m', volume_more_than]))
    if volume_less_than:
        filters.append(EquityQuery('lt', ['avgdailyvol3m', volume_less_than]))
    if dividend_yield_more_than:
        filters.append(EquityQuery('gt', ['forward_dividend_yield', dividend_yield_more_than]))
    if sector:
        filters.append(EquityQuery('eq', ['sector', sector]))
    if industry:
        filters.append(EquityQuery('eq', ['industry', industry]))
    if exchange:
        filters.append(EquityQuery('eq', ['exchange', exchange]))

    # Default to US exchanges if no exchange specified
    if not exchange:
        filters.append(EquityQuery('is-in', ['exchange', 'NMS', 'NYQ', 'ASE']))

    if not filters:
        return json.dumps([])

    query = EquityQuery('and', filters) if len(filters) > 1 else filters[0]

    try:
        result = screen(query, size=limit)
        quotes = result.get('quotes', [])
        stocks = []
        for q in quotes:
            stocks.append({
                'symbol': q.get('symbol'),
                'companyName': q.get('longName') or q.get('shortName'),
                'marketCap': q.get('marketCap'),
                'price': q.get('regularMarketPrice'),
                'beta': q.get('beta'),
                'volume': q.get('regularMarketVolume'),
                'exchange': q.get('fullExchangeName'),
                'dividendYield': q.get('trailingAnnualDividendYield'),
            })
        return json.dumps(stocks)
    except Exception as e:
        return json.dumps({'error': str(e)})


def get_recent_8k(ticker):
    try:
        filings = yf.Ticker(ticker).get_sec_filings()
        eightks = [f for f in filings if f.get('type') == '8-K'][:3]
        return json.dumps([{'date': str(f['date']), 'title': f['title']} for f in eightks])
    except Exception:
        return json.dumps([])


def run_conversation(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "stock_screener",
                    "description": "Screen stocks based on financial criteria using natural language filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market_cap_more_than": {"type": "number", "description": "Minimum market cap in dollars"},
                            "market_cap_less_than": {"type": "number", "description": "Maximum market cap in dollars"},
                            "price_more_than": {"type": "number", "description": "Minimum stock price"},
                            "price_less_than": {"type": "number", "description": "Maximum stock price"},
                            "beta_more_than": {"type": "number", "description": "Minimum beta"},
                            "beta_less_than": {"type": "number", "description": "Maximum beta"},
                            "volume_more_than": {"type": "number", "description": "Minimum average daily volume"},
                            "volume_less_than": {"type": "number", "description": "Maximum average daily volume"},
                            "dividend_yield_more_than": {"type": "number", "description": "Minimum dividend yield as decimal, e.g. 0.02 for 2%"},
                            "sector": {"type": "string", "description": "Sector name, e.g. Technology, Healthcare, Energy, Financial Services, Consumer Cyclical, Industrials, Communication Services, Consumer Defensive, Basic Materials, Real Estate, Utilities"},
                            "industry": {"type": "string", "description": "Industry name"},
                            "exchange": {"type": "string", "description": "Exchange code: NMS for NASDAQ, NYQ for NYSE, ASE for AMEX"},
                            "limit": {"type": "number", "description": "Number of results to return, default 10"},
                        },
                        "required": [],
                    },
                },
            }
        ],
        tool_choice="auto",
    )

    message = response.choices[0].message
    if not message.tool_calls:
        st.write(message.content)
        return

    tool_call = message.tool_calls[0]
    function_args = json.loads(tool_call.function.arguments)

    with st.spinner("Screening stocks..."):
        raw = stock_screener(**function_args)

    data = json.loads(raw)

    if isinstance(data, dict) and 'error' in data:
        st.error(f"Screener error: {data['error']}")
        return
    if not isinstance(data, list) or len(data) == 0:
        st.warning("No stocks matched your criteria. Try broadening your filters.")
        return

    function_response = ""
    with st.spinner("Fetching SEC filings..."):
        for i, stock in enumerate(data):
            stock['8k_filings'] = get_recent_8k(stock['symbol'])
            function_response += (
                f"\n\nStock {i+1}:\n"
                f"- Symbol: {stock['symbol']}\n"
                f"- Company: {stock['companyName']}\n"
                f"- Market Cap: {stock['marketCap']}\n"
                f"- Price: {stock['price']}\n"
                f"- Beta: {stock['beta']}\n"
                f"- Volume: {stock['volume']}\n"
                f"- Exchange: {stock['exchange']}\n"
                f"- Dividend Yield: {stock['dividendYield']}\n"
                f"- Recent 8-K filings: {stock['8k_filings']}"
            )

    placeholder = st.empty()
    second_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a stock screening assistant. Present the results clearly.
Follow these formatting rules:
- Market cap in trillions/billions/millions (e.g. $1.2 billion), 2 decimal places
- Escape $ with backslash (\\$) for markdown
- Price and dividend yield to 2 decimal places
- Beta to 2 decimal places
- Volume in millions (e.g. 5.2M)
- Use clean company names (drop Inc, Corp, Ltd)
- For each stock mention when the last 8-K was filed and its title
- If no stocks found, say so clearly""",
            },
            {"role": "user", "content": user_message},
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": tool_call.id, "content": function_response},
        ],
        stream=True,
    )

    assistant_response = ""
    for chunk in second_response:
        text = chunk.choices[0].delta.content
        if text:
            assistant_response += text
        placeholder.markdown(assistant_response, unsafe_allow_html=True)

    return assistant_response


user_input = st.text_input(
    "Enter your stock screening query",
    placeholder="Ex. show me tech stocks with a market cap greater than 1b and a beta less than 1.5",
)
if st.button("Run"):
    if user_input:
        run_conversation(user_input)
    else:
        st.warning("Please enter a query.")
