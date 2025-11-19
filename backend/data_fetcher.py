import yfinance as yf
import requests
import re
import sys
import os

# --- Import ML/Vector libraries ---
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    import nltk
    from nltk.tokenize import sent_tokenize
except ImportError as e:
    print(f"Error: Missing required libraries: {e}")
    print("Please run: pip install sentence-transformers faiss-cpu numpy nltk")
    sys.exit(1)

# --- Download NLTK data (one-time) ---
def download_nltk_data():
    """
    Downloads the NLTK 'punkt' tokenizer if not found.
    """
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading NLTK tokenizers...")
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            print("NLTK data downloaded successfully.")
        except Exception as e:
            print(f"Warning: Could not download NLTK data: {e}")

# --- Global var to hold the embedding model ---
embedding_model = None

def load_embedding_model():
    """Loads the sentence transformer model into the global variable."""
    global embedding_model
    if embedding_model is None:
        print("Loading embedding model...")
        try:
            # Using a small, fast, and effective model
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Embedding model loaded successfully.")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Don't exit, just return None and let calling code handle it
    return embedding_model

# --- 1. Data Fetching ---

def get_fundamentals(ticker_symbol):
    """
    Fetches fundamental stock data using yfinance.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # Extract key financial indicators with safe defaults
        fundamentals = {
            "Market Cap": info.get('marketCap', 'N/A'),
            "P/E Ratio (Trailing)": info.get('trailingPE', 'N/A'),
            "P/E Ratio (Forward)": info.get('forwardPE', 'N/A'),
            "Price-to-Book (P/B)": info.get('priceToBook', 'N/A'),
            "PEG Ratio": info.get('pegRatio', 'N/A'),
            "Dividend Yield": info.get('dividendYield', 'N/A'),
            "Earnings per Share (EPS)": info.get('trailingEps', 'N/A'),
            "Return on Equity (ROE)": info.get('returnOnEquity', 'N/A'),
            "Debt-to-Equity": info.get('debtToEquity', 'N/A'),
            "52 Week High": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52 Week Low": info.get('fiftyTwoWeekLow', 'N/A'),
            "Current Price": info.get('currentPrice', 'N/A'),
        }
        
        # Get the long business summary
        summary = info.get('longBusinessSummary', 'No summary available.')
        
        return fundamentals, summary
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker_symbol}: {e}")
        # Return empty but valid data instead of None
        return {}, "No fundamental data available."

def get_news(ticker_symbol, api_key, num_articles=10):  # Reduced from 20 to 10
    """
    Fetches recent news articles from NewsAPI.org.
    """
    if not api_key:
        print("Error: NewsAPI key not provided")
        return []
        
    base_url = "https://newsapi.org/v2/everything"  # FIXED: Removed markdown formatting
    params = {
        'q': ticker_symbol,
        'apiKey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': num_articles
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            print(f"Found {len(articles)} news articles for {ticker_symbol}")
            return articles
        else:
            print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {ticker_symbol}: {e}")
        return []

# --- 2. RAG Processing ---

def process_and_embed(news_articles, summary_text, ticker=""):
    """
    Processes text into chunks, creates embeddings, and builds a FAISS index.
    """
    if embedding_model is None:
        load_embedding_model()
    
    if embedding_model is None:
        print("Error: Embedding model not available")
        return None, [], []
        
    text_chunks = []
    metadata = []
    
    # --- 1. Process the summary text ---
    if summary_text and summary_text != 'No summary available.':
        try:
            summary_sentences = sent_tokenize(summary_text)
            # Create chunks of 3 sentences
            for i in range(0, len(summary_sentences), 3):
                chunk = " ".join(summary_sentences[i:i+3])
                text_chunks.append(chunk)
                metadata.append({
                    'source': f"{ticker} Business Summary",
                    'date': 'N/A',
                    'url': '#'
                })
        except Exception as e:
            print(f"Error processing summary text: {e}")

    # --- 2. Process news articles ---
    for article in news_articles:
        try:
            content = article.get('description', '') or article.get('content', '')
            if not content:
                continue
            
            # Clean up the text
            content = re.sub(r'\[\+\d+ chars\]$', '', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            if not content:
                continue
                
            sentences = sent_tokenize(content)
            # Create smaller chunks for memory efficiency
            for i in range(0, len(sentences), 3):  # Reduced from 4 to 3
                chunk = " ".join(sentences[i:i+3])
                text_chunks.append(chunk)
                metadata.append({
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'date': article.get('publishedAt', 'Unknown')[:10],
                    'url': article.get('url', '#')
                })
        except Exception as e:
            print(f"Error processing news article: {e}")
            continue

    # --- 3. Create Embeddings & FAISS Index ---
    if not text_chunks:
        print("No text chunks to embed.")
        return None, [], []

    try:
        print(f"Creating embeddings for {len(text_chunks)} text chunks...")
        
        # Process in smaller batches to avoid memory issues
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i+batch_size]
            batch_embeddings = embedding_model.encode(batch, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(all_embeddings).astype('float32')
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        print(f"FAISS index built with {index.ntotal} vectors.")
        return index, text_chunks, metadata
        
    except Exception as e:
        print(f"Error creating FAISS index: {e}")
        return None, [], []

# Remove or comment out the self-test block for production
# if __name__ == "__main__":
#     # Test code removed for production deployment
#     pass
