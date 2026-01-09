import streamlit as st
import requests
import newspaper4k
from newspaper import Article

# Replace with your actual Google API Key
API_KEY = "AIzaSyAHVk5oi3wOoS7su-EJNLOi88d8VYGHjrw"

def get_article_text(url):
    """Extracts text from a news URL."""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        # 1. Fetch the HTML manually
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 401:
            return None, "Access Denied (401). Reuters is blocking automated access. Copy/paste the text manually."
        elif response.status_code != 200:
            return None, f"Failed to reach site (Status {response.status_code})."

        # 2. Feed the HTML into the article object
        # In newspaper4k/3k, we use the article constructor directly
        article = newspaper.Article(url)
        article.download(input_html=response.text) # This injects HTML instead of downloading
        article.parse()
        
        return article.title, article.text

    except Exception as e:
        return None, f"Error: {str(e)}"


def check_fact(query):
    """Queries the Google Fact Check Tools API."""
    url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query="+query+"&key="+API_KEY
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('claims', [])
    return []

# --- Streamlit UI ---
st.set_page_config(page_title="2026 Fact Checker", page_icon="📰")
st.title("📰 Real-Time News Verifier")
st.write("Verify claims by pasting a **link** or **news text**.")

# Input Selection
input_type = st.radio("Select Input Type:", ("News Link (URL)", "Raw Text / Headline"))

if input_type == "News Link (URL)":
    user_input = st.text_input("Paste news link here:")
else:
    user_input = st.text_area("Paste news text or headline here:", height=150)

if st.button("Verify Now"):
    search_query = ""
    
    if input_type == "News Link (URL)" and user_input:
        with st.spinner("Extracting content..."):
            title, content = get_article_text(user_input)
            if title:
                st.subheader(f"Title: {title}")
                search_query = title  # Use title for the fact-check search
            else:
                st.error(content)
    else:
        search_query = user_input

    if search_query:
        with st.spinner("Checking global fact-check databases..."):
            results = check_fact(search_query)
            
            if results:
                st.success(f"Found {len(results)} relevant fact-checks:")
                for claim in results:
                    text = claim.get('text', 'No claim text')
                    review = claim.get('claimReview', [{}])[0]
                    rating = review.get('textualRating', 'Unknown')
                    source = review.get('publisher', {}).get('name', 'Unknown Source')
                    link = review.get('url', '#')
                    
                    with st.expander(f"Verdict: {rating} (by {source})"):
                        st.write(f"**Original Claim:** {text}")
                        st.write(f"**Rating:** {rating}")
                        st.write(f"[Read full report]({link})")
            else:
                st.warning("No existing fact-checks found for this specific claim. Proceed with caution.")
    else:
        st.info("Please provide a link or text to analyze.")

