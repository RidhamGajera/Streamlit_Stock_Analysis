import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Stock Market Application", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for styling
st.markdown("""
    <style>
    body {
        background-color: #f5f5f5;
        color: #333333;
    }
    .main {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
    }
    .stButton>button {
        background-color: #007bff;
        color: #ffffff;
    }
    .stSelectbox, .stTextInput, .stDateInput {
        border: 1px solid #ced4da;
        border-radius: 5px;
    }
    .news-box {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .news-title {
        margin: 0;
        color: #007bff;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for input
st.sidebar.title("Stock Search")
stock_input = st.sidebar.text_input("Enter Stock Symbol or Name", "AAPL")
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", date.today())

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock
    except Exception as e:
        st.error(f"Failed to retrieve data for {ticker}: {e}")
        return None

def format_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return str(value)

def display_stock_info(stock):
    stock_info = stock.info

    st.title(f"{stock_info.get('longName', stock_info.get('shortName', 'N/A'))} ({stock_info.get('symbol', 'N/A')})")

    # Valuation Measures Table
    st.header("Valuation Measures")
    valuation_measures = {
        "Market Cap": stock_info.get('marketCap'),
        "PE Ratio": stock_info.get('trailingPE'),
        "Price/Book": stock_info.get('priceToBook'),
        "Forward PE": stock_info.get('forwardPE'),
        "Dividend Yield (%)": stock_info.get('dividendYield') * 100 if stock_info.get('dividendYield') else "N/A"
    }
    st.table(pd.DataFrame(list(valuation_measures.items()), columns=['Metric', 'Value']))

    # Financial Highlights Table
    st.header("Financial Highlights")
    financial_highlights = {
        "Total Revenue": stock_info.get('totalRevenue'),
        "Gross Profits": stock_info.get('grossProfits'),
        "EBITDA": stock_info.get('ebitda'),
        "Net Income": stock_info.get('netIncomeToCommon'),
        "Operating Cash Flow": stock_info.get('operatingCashflow')
    }
    st.table(pd.DataFrame(list(financial_highlights.items()), columns=['Metric', 'Value']))

    # Stock Price Chart
    st.header("Stock Price Chart")
    data = stock.history(start=start_date, end=end_date)
    if not data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
        fig.update_layout(title="Stock Price Over Time", xaxis_title="Date", yaxis_title="Price (USD)")
        st.plotly_chart(fig)
    else:
        st.write("No data available for the selected date range.")

def display_balance_sheet(stock):
    st.header("Balance Sheet")
    try:
        balance_sheet = stock.balance_sheet
        if not balance_sheet.empty:
            st.write(balance_sheet)
        else:
            st.write("No balance sheet data available.")
    except Exception as e:
        st.error(f"Error fetching balance sheet data: {e}")

def display_cash_flow(stock):
    st.header("Cash Flow")
    try:
        cash_flow = stock.cashflow
        if not cash_flow.empty:
            st.write(cash_flow)
        else:
            st.write("No cash flow data available.")
    except Exception as e:
        st.error(f"Error fetching cash flow data: {e}")

def get_market_news():
    try:
        url = "https://finance.yahoo.com/topic/stock-market-news/"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('li', class_='js-stream-content')
        news_list = []
        for article in articles:
            title = article.find('h3')
            link = article.find('a', href=True)
            if title and link:
                news_list.append({
                    'title': title.get_text(),
                    'link': 'https://finance.yahoo.com' + link['href']
                })
        return news_list
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching market news: {e}")
        return None

def display_market_news(num_articles=5):
    st.header("Stock Market News")
    news_list = get_market_news()
    if news_list:
        for news in news_list[:num_articles]:
            st.markdown(
                f'<div class="news-box">'
                f'<h4><a class="news-title" href="{news["link"]}" target="_blank">{news["title"]}</a></h4>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.write("No stock market news available.")

# Main app functionality
if stock_input:
    stock = get_stock_info(stock_input)
    if stock:
        display_stock_info(stock)
        st.markdown("---")
        display_balance_sheet(stock)
        st.markdown("---")
        display_cash_flow(stock)
        st.markdown("---")
        # User input to select number of news articles to display
        num_articles = st.sidebar.slider("Number of news articles to display:", 1, 20, 5)
        display_market_news(num_articles)
else:
    st.write("Please enter a stock symbol or name in the sidebar to start.")
