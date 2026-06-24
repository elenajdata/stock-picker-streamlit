import streamlit as st
from openai import OpenAI
import requests
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

st.title("Stock Screener")
st.write("Ask in plain English — get a summary of matching stocks and their latest SEC filings.")


def stock_screener(market_cap_more_than=None, market_cap_less_than=None, price_more_than=None, price_less_than=None, beta_more_than=None, beta_less_than=None, volume_more_than=None, volume_less_than=None, dividend_more_than=None, dividend_less_than=None, is_etf=False, is_actively_trading=False, sector=None, industry=None, country='US', exchange=None, limit=None):
    base_url = 'https://financialmodelingprep.com/api/v3/stock-screener'

    params = {
        'apikey': FMP_API_KEY,
        'marketCapMoreThan': market_cap_more_than,
        'marketCapLowerThan': market_cap_less_than,
        'priceMoreThan': price_more_than,
        'priceLowerThan': price_less_than,
        'betaMoreThan': beta_more_than,
        'betaLowerThan': beta_less_than,
        'volumeMoreThan': volume_more_than,
        'volumeLowerThan': volume_less_than,
        'dividendMoreThan': dividend_more_than,
        'dividendLowerThan': dividend_less_than,
        'isEtf': is_etf,
        'isActivelyTrading': is_actively_trading,
        'sector': sector,
        'industry': industry,
        'country': country,
        'exchange': exchange,
        'limit': limit if limit is not None else 10,
    }

    params = {k: v for k, v in params.items() if v is not None}

    response = requests.get(base_url, params=params)

    st.expander("API Call").write(response.url)

    return json.dumps(response.json())


def get_8k(ticker):
    base_url = f'https://financialmodelingprep.com/api/v3/sec_filings/{ticker}'
    params = {
        'apikey': FMP_API_KEY,
        'type': '8-k',
        'page': 0,
    }
    response = requests.get(base_url, params=params)
    return json.dumps(response.json()[:5])


def run_conversation(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "stock_screener",
                    "description": "Fetch stock screening data from the FMP API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market_cap_more_than": {"type": "number"},
                            "market_cap_less_than": {"type": "number"},
                            "price_more_than": {"type": "number"},
                            "price_less_than": {"type": "number"},
                            "beta_more_than": {"type": "number"},
                            "beta_less_than": {"type": "number"},
                            "volume_more_than": {"type": "number"},
                            "volume_less_than": {"type": "number"},
                            "dividend_more_than": {"type": "number"},
                            "dividend_less_than": {"type": "number"},
                            "is_etf": {"type": "boolean"},
                            "is_actively_trading": {"type": "boolean"},
                            "sector": {"type": "string"},
                            "industry": {"type": "string"},
                            "country": {"type": "string"},
                            "exchange": {"type": "string"},
                            "limit": {"type": "number"},
                        },
                        "required": [],
                    },
                },
            }
        ],
        tool_choice="auto",
    )

    message = response.choices[0].message
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        function = globals()[function_name]

        data = json.loads(function(
            market_cap_more_than=function_args.get("market_cap_more_than"),
            market_cap_less_than=function_args.get("market_cap_less_than"),
            price_more_than=function_args.get("price_more_than"),
            price_less_than=function_args.get("price_less_than"),
            beta_more_than=function_args.get("beta_more_than"),
            beta_less_than=function_args.get("beta_less_than"),
            volume_more_than=function_args.get("volume_more_than"),
            volume_less_than=function_args.get("volume_less_than"),
            dividend_more_than=function_args.get("dividend_more_than"),
            dividend_less_than=function_args.get("dividend_less_than"),
            is_etf=function_args.get("is_etf"),
            is_actively_trading=function_args.get("is_actively_trading", True),
            sector=function_args.get("sector"),
            industry=function_args.get("industry"),
            country=function_args.get("country"),
            exchange=function_args.get("exchange", "NASDAQ,NYSE,AMEX"),
            limit=function_args.get("limit", 10),
        ))

        function_response = ""
        for i, stock_info in enumerate(data):
            stock_info["8k"] = get_8k(stock_info['symbol'])
            function_response += (
                f"\n\nStock {i+1}:\n"
                f"- Symbol: {stock_info['symbol']}\n"
                f"- Company Name: {stock_info['companyName']}\n"
                f"- Market Cap: {stock_info['marketCap']}\n"
                f"- Sector: {stock_info['sector']}\n"
                f"- Industry: {stock_info.get('industry', 'N/A')}\n"
                f"- Beta: {stock_info['beta']}\n"
                f"- Volume: {stock_info['volume']}\n"
                f"- Exchange: {stock_info['exchange']}\n"
                f"- Last Annual Dividend: {stock_info['lastAnnualDividend']}\n"
                f"- Last 8k: {stock_info['8k']}"
            )

        placeholder_response = st.empty()
        second_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a stock screening assistant designed to help users find stocks based on natural language inputs. You can find stocks based on market capitalization, price, beta, volume, dividend, ETF status, actively trading status, sector, industry, country, and exchange.
            Follow these instructions in your response:
                - Market capitalization should always be in trillion, billion, or million (i.e 1 billion instead of 1000000000)
                - Also use human readable format for price, beta, volume, and dividend (i.e 1 billion instead of 1000000000)
                - Use 2 decimal places for market cap, price, beta, volume, and dividend
                - Write company names in human readable format for company names (i.e exclude Inc, Ltd, etc.)
                - add $ in front of market capitalization, price, and dividend - but escape it with a backslash (i.e \\$) for markdown formatting
                - Only respond if there is an API response, if not say that there are no stocks that match the criteria
                - Tell when last 8k was filed for each stock
              """,
                },
                {"role": "user", "content": user_message},
                {
                    "role": "assistant",
                    "content": message.content if message.content else "Initiating function call...",
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response,
                },
            ],
            stream=True,
        )

        assistant_response = ""
        for chunk in second_response:
            r_text = chunk.choices[0].delta.content
            if r_text is not None:
                assistant_response += r_text
            placeholder_response.markdown(assistant_response, unsafe_allow_html=True)
        return assistant_response


user_input = st.text_input(
    "Enter your stock screening query",
    placeholder="Ex. show me tech stocks with a market cap greater than 1b and a beta less than 1.5",
)
if st.button("Run"):
    run_conversation(user_input)
