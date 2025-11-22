import streamlit as st
import yfinance as yf
import requests
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Market Sentiment AI", page_icon="💰", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("ℹ️ About the App")
    st.markdown("""
    **Data Source:** Market data is sourced dynamically from [Yahoo Finance](https://finance.yahoo.com/).
    **AI Engine:** Sentiment analysis powered by [FinBERT](https://huggingface.co/ProsusAI/finbert).
    **Version:** 6.0 (Stable)
    """)
    st.divider()
    st.caption("Built by Ashish Kumar Kirar")

# --- 2. THE AI BRAIN ---
def get_sentiment(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
    try:
        token = st.secrets["HF_TOKEN"]
    except:
        return "Error", 0.0

    headers = {"Authorization": f"Bearer {token}"}
    
    if text and len(text) > 1500:
        text = text[:1500]
        
    payload = {"inputs": text}

    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list): scores = data[0]
                else: scores = data
                top = sorted(scores, key=lambda x: x['score'], reverse=True)[0]
                return top['label'], top['score']
            elif 'error' in data and 'loading' in data['error']:
                time.sleep(3)
                continue
            elif 'error' in data:
                return "Neutral", 0.0
        except:
            pass
    return "Neutral", 0.0

# --- 3. HELPER FUNCTIONS ---
def search_symbols(query):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "quotesCount": 10, "newsCount": 0} 
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        if 'quotes' in data and len(data['quotes']) > 0:
            results = []
            for q in data['quotes']:
                if 'symbol' in q:
                    results.append({
                        'symbol': q['symbol'],
                        'name': q.get('longname', q.get('shortname', q['symbol'])),
                        'exchange': q.get('exchDisp', q.get('exchange', 'Unknown'))
                    })
            return results
    except:
        pass
    return []

def sentiment_card(title, link, publisher, date_str, label, score):
    color = "#777"
    if label == "positive": color = "#28a745"
    elif label == "negative": color = "#dc3545"
    
    st.markdown(f"""
    <div style="padding: 12px; border-left: 5px solid {color}; background-color: #f0f2f6; margin-bottom: 10px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between;">
            <span style="color:{color}; font-weight:bold; font-size: 0.9em;">{label.upper()} ({score:.0%})</span>
            <span style="color: #666; font-size: 0.8em;">{date_str}</span>
        </div>
        <div style="margin-top: 5px;">
            <a href="{link}" target="_blank" style="color: #1f1f1f; text-decoration: none; font-weight: 600; font-size: 1.1em;">{title}</a>
        </div>
        <div style="margin-top: 5px; font-size: 0.8em; color: #666;">
            Source: {publisher}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. THE UI ---
st.title("💰 Market Sentiment AI (v6.0)")

tab1, tab2 = st.tabs(["📈 Stock Dashboard", "🧪 Custom Analysis"])

with tab1:
    query = st.text_input("Enter Company Name:")
    if query:
        with st.spinner(f"🔍 Searching for '{query}'..."):
            search_results = search_symbols(query)

        if search_results:
            options = {f"{r['name']} ({r['symbol']}) - {r['exchange']}": r['symbol'] for r in search_results}
            selected_label = st.selectbox("Select the correct company:", list(options.keys()))
            
            if selected_label:
                ticker = options[selected_label]
                stock = yf.Ticker(ticker)
                try:
                    hist = stock.history(period="1mo")
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        if len(hist) >= 2:
                            prev = hist['Close'].iloc[-2]
                            delta = current - prev
                        else:
                            delta = 0
                            st.warning("⚠️ Limited trading data found.")

                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.metric("Price", f"{current:.2f}", f"{delta:.2f}")
                        with col2:
                            chart_data = hist[['Close']].copy()
                            chart_data.index = chart_data.index.date
                            st.line_chart(chart_data, height=250)
                        
                        st.subheader(f"🧠 AI News Analysis for {ticker}")
                        progress_bar = st.progress(0, text="Scanning news...")
                        
                        news_list = stock.news
                        if news_list:
                            for i, item in enumerate(news_list[:5]):
                                progress_bar.progress((i + 1) * 20, text=f"Reading Headline {i+1}...")
                                
                                # --- THE TITANIUM SHIELD ---
                                try:
                                    # 1. Normalize Payload
                                    if isinstance(item, dict) and 'content' in item and item['content']:
                                        payload = item['content']
                                    else:
                                        payload = item
                                    
                                    if not payload: continue

                                    # 2. Safe Extraction
                                    title = payload.get('title', 'No Title')
                                    
                                    # Date
                                    pub_time = payload.get('pubDate') or payload.get('providerPublishTime')
                                    date_str = "Recent"
                                    if pub_time:
                                        try:
                                            dt = datetime.fromisoformat(str(pub_time).replace("Z", "+00:00"))
                                            date_str = dt.strftime("%b %d, %Y")
                                        except:
                                            pass

                                    # Provider (Source) - Extra Safe
                                    provider_data = payload.get('provider')
                                    if provider_data and isinstance(provider_data, dict):
                                        publisher = provider_data.get('displayName', 'Unknown')
                                    else:
                                        publisher = "Unknown"
                                        
                                    # Link - Extra Safe
                                    click_data = payload.get('clickThroughUrl')
                                    if click_data and isinstance(click_data, dict):
                                        link = click_data.get('url', '#')
                                    else:
                                        link = payload.get('link', '#')

                                    # 3. AI Call & Render
                                    label, score = get_sentiment(title)
                                    sentiment_card(title, link, publisher, date_str, label, score)
                                    
                                except Exception as e:
                                    # If ANYTHING breaks in this item, skip it and continue loop
                                    continue 
                                # ---------------------------
                            
                            progress_bar.empty()
                        else:
                            st.info("No news found.")
                    else:
                        st.error("No trading data.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("No companies found.")

with tab2:
    st.subheader("🧪 Test Your Own Text")
    user_text = st.text_area("Paste text here:", height=150)
    if st.button("Analyze Text"):
        if user_text:
            with st.spinner("AI is thinking..."):
                label, score = get_sentiment(user_text)
                color = "gray"
                if label == "positive": color = "green"
                elif label == "negative": color = "red"
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;">
                    <h2 style="color: {color}; margin:0;">{label.upper()}</h2>
                    <p style="font-size: 1.5em; margin:0;">Confidence: <strong>{score:.1%}</strong></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Please enter text.")