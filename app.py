# Importing all the necessary libraries
# Importing Streamlit library for the frontend interface on Streamlit platform
import streamlit as st
# Importing Yahoo Finance library to fetch stock data
import yfinance as yf
# Importing requests library to make HTTP requests to external APIs
import requests
# Importing time and datetime for handling time-related operations
import time
from datetime import datetime

# Setting up the Streamlit page configuration and adding Title and Icon to the app and setting layout to wide 
st.set_page_config(page_title="Market Sentiment AI", page_icon="💰", layout="wide")

# Configuring the sidebar with app info, disclaimer and Built By credit
# Using 'with' method to add multiple elements to the sidebar 
with st.sidebar:
    
    # Setting a Header for the sidebar
    st.header("ℹ️ About the App")
    
    # Using Streamlit's 'markdown' method to add formatted text for 'Data Source', 'AI Engine' and 'Disclaimer'
    st.markdown("""
    **Data Source:** Market data is sourced dynamically from [Yahoo Finance](https://finance.yahoo.com/).
    
    **AI Engine:** Sentiment analysis powered by [FinBERT](https://huggingface.co/ProsusAI/finbert) via Hugging Face.
    
    **Disclaimer:** This tool is for educational purposes only. Do not use this as the sole basis for investment decisions.
    """)

    # Adding a divider line for better visual separation
    st.divider()
    # Adding a credit line with my full name at the bottom of the sidebar
    st.caption("Built by Ashish Kumar Kirar")

# Defining function to get the sentiment of the given text using FinBERT model from Hugging Face
def get_sentiment(text):
    # Storing Hugging Face's FinBERT Inference API URL to a variable
    API_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
    
    # Safety Net: Attempts to get the API key. If it fails, fail gracefully instead of crashing
    try:
        # Retrieving Hugging Face API Token from Streamlit sectets file
        token = st.secrets["HF_TOKEN"]
    except:
        # If token retrieval fails, return default error sentiment and prevents from
        # crashing and instead, reports that we failed ("Error") with 0.0 confidence score
        return "Error", 0.0

    # Setting up the headers for the API request with Authorization Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Truncate text to prevent errors (BERT limit)
    if text and len(text) > 1500:
        text = text[:1500]
    
    # Preparing the payload with the input text
    payload = {"inputs": text}

    # Making the POST request to the Hugging Face API with retries for loading state
    for attempt in range(3):
        # Using Try-Except block to handle potential errors during the API request
        try:
            # Making the POST request to the API URL with headers and payload
            response = requests.post(API_URL, headers=headers, json=payload)
            # Parsing the JSON response from the API
            data = response.json()
            
            # Handling different response structures using if-elif conditions
            # 1. If the response is a list with at least one element
            if isinstance(data, list) and len(data) > 0:
                # Nested if to handle cases where the first element is also a list
                if isinstance(data[0], list): scores = data[0]
                # Else, use the data as is
                else: scores = data
                
                # Sorting the scores to find the label with the highest score
                top = sorted(scores, key=lambda x: x['score'], reverse=True)[0]
                # Returning the top label and its score
                return top['label'], top['score']
            
            # 2. If the response contains an 'error' key with 'loading' message
            elif 'error' in data and 'loading' in data['error']:
                # Wait for 3 seconds before retrying
                time.sleep(3)
                # continue to the next attempt
                continue
            
            # 3. If the response contains an 'error' key with other messages
            elif 'error' in data:
                # Return 'Error' label with 0.0 score
                return "Neutral", 0.0

        # Catching any exceptions that occur during the request or processing        
        except:
            # If an exception occurs, we simply pass and try again
            pass

    # After retries, if we still fail, return 'Neutral' with 0.0 score        
    return "Neutral", 0.0

# --- 3. HELPER FUNCTIONS --- to search for stock symbols using Yahoo Finance API
def search_symbols(query):
    # Yahoo Finance Search API Endpoint
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    # Setting up parameters for the search query
    params = {"q": query, "quotesCount": 10, "newsCount": 0} 
    # Setting up headers to mimic a browser request
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Making the GET request to the Yahoo Finance Search API using try-except for error handling
    try:
        # Making the GET request to the Yahoo Finance Search API
        r = requests.get(url, params=params, headers=headers)
        # Parsing the JSON response
        data = r.json()
        # Checking if 'quotes' key exists in the response data
        if 'quotes' in data and len(data['quotes']) > 0:
            # Extracting relevant information from each quote and storing it in a list named 'results'
            results = []
            # Looping through each quote in the response data
            for q in data['quotes']:
                # Ensuring that the quote has a 'symbol' key before processing
                if 'symbol' in q:
                    # Appending a dictionary with symbol, name, and exchange to the results list
                    results.append({
                        'symbol': q['symbol'],
                        'name': q.get('longname', q.get('shortname', q['symbol'])),
                        'exchange': q.get('exchDisp', q.get('exchange', 'Unknown'))
                    })
            # Returning the list of results        
            return results
    # Catching any exceptions that occur during the request or processing    
    except:
        # If an exception occurs, we simply pass and return an empty list
        pass
    return []

# Function to render sentiment card in Streamlit
def sentiment_card(title, link, publisher, date_str, label, score):
    # Color Logic
    color = "#777" # Default Grey
    if label == "positive": color = "#28a745" # Green
    elif label == "negative": color = "#dc3545" # Red
    
    # Formatting the Label
    label_text = label.title() 
    
    # Rendering the card using Streamlit's markdown with HTML/CSS for styling
    st.markdown(f"""
    <div style="padding: 15px; border-left: 5px solid {color}; background-color: #f0f2f6; margin-bottom: 15px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color:{color}; font-weight:bold; font-size: 1.0em;">
                Sentiment: {label_text} <span style="color: #555; font-weight: normal;">(with {score:.0%} confidence)</span>
            </span>
            <span style="color: #888; font-size: 0.8em;">{date_str}</span>
        </div>
        <div style="margin-top: 8px;">
            <a href="{link}" target="_blank" style="color: #1f1f1f; text-decoration: none; font-weight: 600; font-size: 1.1em; line-height: 1.4;">{title}</a>
        </div>
        <div style="margin-top: 8px; font-size: 0.85em; color: #666;">
            Source: {publisher}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. THE UI ---
# Setting the main title of the app
st.title("💰 Market Sentiment AI")

# Creating two tabs for the app: Stock Dashboard and Custom Analysis
tab1, tab2 = st.tabs(["📈 Stock Dashboard", "🧪 Custom Analysis"])

# --- TAB 1: DASHBOARD ---
# Using 'with' method to add multiple elements to Tab 1
with tab1:
    # input box for entering company name
    query = st.text_input("Enter Company Name (e.g., Apple, Samsung, Genpact, etc.):")

    # If block to handle the search and display results when a query is entered
    # 1. Search for symbols matching the query, if query is not empty
    if query:
        # Display a loading spinner while searching
        with st.spinner(f"🔍 Searching for '{query}'..."):
            # 2. Call the search_symbols function to get matching companies
            search_results = search_symbols(query)

        # 3. If search results are found, display a dropdown to select the correct company
        if search_results:
            # Creating a dictionary of options for the selectbox
            options = {f"{r['name']} ({r['symbol']}) - {r['exchange']}": r['symbol'] for r in search_results}
            # 4. Displaying the selectbox for company selection
            selected_label = st.selectbox("Select the correct company:", list(options.keys()))

            # 5. If a company is selected, fetch and display stock data and news sentiment analysis
            if selected_label:
                # Fetching stock data for the selected ticker
                ticker = options[selected_label]
                stock = yf.Ticker(ticker)
                # Fetching historical market data for the past month and handling potential errors using try-except block
                try:
                    # 6. Fetch historical data for the past month
                    hist = stock.history(period="1mo")
                    # Check if historical data is not empty
                    if not hist.empty:
                        # Metrics (Safe Mode)
                        current = hist['Close'].iloc[-1]
                        # Calculate price change from previous close safely, if length of historical is more than 2
                        if len(hist) >= 2:
                            # Calculate delta
                            # storing previous close price in variable 'prev'
                            prev = hist['Close'].iloc[-2]
                            # calculating delta as difference between current and previous close price
                            delta = current - prev
                        # If not enough data, set delta to 0 and show warning
                        else:
                            delta = 0
                            st.warning("⚠️ Note: Limited trading data found for this ticker.")

                        # Displaying Metrics and Chart
                        # Using Streamlit's columns to layout metrics and chart side by side
                        col1, col2 = st.columns([1, 3])
                        # Displaying current price and delta in the first column
                        with col1:
                            st.metric("Price", f"{current:.2f}", f"{delta:.2f}")
                        # Displaying line chart of historical closing prices in the second column
                        with col2:
                            # Sanitize chart data (Timezone Fix)
                            # copying 'Close' column from historical data to 'chart_data' and dtoring in variable 'chart_data' to plot
                            chart_data = hist[['Close']].copy()
                            # Converting index to date only for better x-axis labels
                            chart_data.index = chart_data.index.date
                            # Plotting the line chart using Streamlit's line_chart method
                            st.line_chart(chart_data, height=250)

                        # Streamlit subheader for AI News Analysis section
                        st.subheader(f"🧠 AI News Analysis for {ticker}")
                        # Setting up a progress bar to indicate news scanning progress and storing in variable 'progress_bar'
                        progress_bar = st.progress(0, text="Scanning news...")
                        
                        # Fetching news articles related to the stock
                        news_list = stock.news
                        # If news articles are found, analyze sentiment for top 5 articles
                        if news_list:
                            # Looping through top 5 news articles
                            for i, item in enumerate(news_list[:5]):
                                # Updating progress bar simultaneously
                                progress_bar.progress((i + 1) * 20, text=f"Reading Headline {i+1}...")
                                
                                # --- TITANIUM SHIELD LOGIC START ---
                                # Using Try-Except block to handle any potential errors in processing each news item
                                try:
                                    # 1. Normalize Payload (Handle nested content)
                                    # Check if 'item' is a dict and has 'content' key with non-empty value
                                    if isinstance(item, dict) and 'content' in item and item['content']:
                                        # If so, use the nested 'content' as the payload
                                        payload = item['content']
                                    # else if 'item' has 'title' key, use 'item' itself as payload
                                    else:
                                        payload = item
                                    
                                    # Skip if payload is None or empty
                                    if not payload: continue

                                    # 2. Safe Extraction of Required Fields
                                    # Title Logic
                                    title = payload.get('title', 'No Title Available')
                                    
                                    # Date Logic
                                    # Trying to get publication date from 'pubDate' or 'providerPublishTime'
                                    pub_time = payload.get('pubDate') or payload.get('providerPublishTime')
                                    # Default date string
                                    date_str = "Recent"
                                    # Converting pub_time to readable date format
                                    # if pub_time exists
                                    if pub_time:
                                        # Using Try-Except to handle different date formats
                                        try:
                                            # ISO Format with 'Z' timezone handling
                                            dt = datetime.fromisoformat(str(pub_time).replace("Z", "+00:00"))
                                            # Formatting date to "MMM DD, YYYY"
                                            date_str = dt.strftime("%b %d, %Y")
                                        except:
                                            # Fallback: Unix Timestamp handling
                                            try:
                                                # Converting pub_time to integer and then to datetime
                                                dt = datetime.fromtimestamp(int(pub_time))
                                                date_str = dt.strftime("%b %d, %Y")
                                            # if conversion fails, silently pass
                                            except:
                                                pass

                                    # Provider Logic
                                    # Trying to get publisher name from 'provider' key
                                    provider = payload.get('provider', {})
                                    # Checking if provider is a dict and has 'displayName' key
                                    if isinstance(provider, dict):
                                        # Getting publisher name safely
                                        publisher = provider.get('displayName', 'Unknown')
                                    # Else, if provider is a list with at least one element    
                                    else:
                                        publisher = "Unknown"
                                        
                                    # Link Logic
                                    # Trying to get clickThroughUrl or link from payload
                                    click_url = payload.get('clickThroughUrl')
                                    # If click_url is a dict, extract 'url' key
                                    if click_url and isinstance(click_url, dict):
                                        link = click_url.get('url', '#')
                                    # otherwise, use 'link' key
                                    else:
                                        link = payload.get('link', '#')

                                    # 3. AI Call & Render
                                    # Getting sentiment label and score using the get_sentiment function
                                    label, score = get_sentiment(title)
                                    sentiment_card(title, link, publisher, date_str, label, score)

                                # Catching any exceptions that occur during processing of this news item    
                                except Exception as e:
                                    # If ANYTHING breaks in this item, skip it silently and continue loop
                                    continue 
                                # --- TITANIUM SHIELD LOGIC END ---
                            
                            # Clear progress bar after processing all news
                            progress_bar.empty()
                        # If no news articles are found, display an info message
                        else:
                            st.info("No news found.")
                    
                    else:
                        st.error(f"No trading data found for {ticker}.")
                
                # Catching any exceptions that occur during fetching or processing stock data
                except Exception as e:
                    st.error(f"Error: {e}")
        # If no search results are found, display a warning message
        else:
            st.warning("No companies found. Try a different name.")

# --- TAB 2: CUSTOM ANALYSIS ---
# Using 'with' method to add multiple elements to Tab 2
with tab2:
    # Streamlit subheader for Custom Text Analysis section
    st.subheader("🧪 Test Your Own Text")
    # Text area for user to input custom text for sentiment analysis
    user_text = st.text_area("Paste text here:", height=150)
    # Button to trigger sentiment analysis, when clicked
    if st.button("Analyze Text"):
        # If user has entered text, proceed with sentiment analysis
        # 1. If user_text is not empty
        if user_text:
            # Displaying a loading spinner while AI processes the text
            with st.spinner("AI is thinking..."):
                label, score = get_sentiment(user_text)
                
                # UX Update for Custom Tab
                color = "#777"
                if label == "positive": color = "#28a745"
                elif label == "negative": color = "#dc3545"
                # Formatting the Label as Title
                label_text = label.title()
                
                # Rendering the sentiment result card using Streamlit's markdown with HTML/CSS for styling
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; border: 1px solid #ddd;">
                    <h2 style="color: {color}; margin:0;">Sentiment: {label_text}</h2>
                    <p style="font-size: 1.2em; margin:0; color: #555;">with <strong>{score:.1%}</strong> confidence</p>
                </div>
                """, unsafe_allow_html=True)
        # 2. If user_text is empty, display a warning message
        else:
            st.warning("Please enter text.")