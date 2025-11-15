import uvicorn
import sqlite3
import time
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- Import from our other files ---
# These imports come from your existing data_fetcher.py and ai_logic.py
try:
    # We also need load_embedding_model from data_fetcher
    from data_fetcher import get_fundamentals, get_news, process_and_embed, load_embedding_model
    from ai_logic import retrieve_relevant_chunks, build_prompt, get_analysis
except ImportError as e:
    print(f"Error: Could not import from data_fetcher.py or ai_logic.py: {e}")
    print("Please make sure all .py files are in the same directory.")
    sys.exit(1)

# --- !! IMPORTANT !! ---
# Load API keys from Environment Variables (set in Render dashboard)
YOUR_API_KEY = os.environ.get("YOUR_API_KEY")
if not YOUR_API_KEY:
    print("Error: YOUR_API_KEY (for NewsAPI) is not set as an environment variable.")
    sys.exit(1)

# --- 1. Define API Models ---
# This Pydantic model *must* match the data your React form sends
class AnalysisRequest(BaseModel):
    ticker: str
    financialCondition: List[str]
    expectedReturn: int
    riskTolerance: str
    tradingPreferences: str

# --- 2. Initialize FastAPI App ---
app = FastAPI()

# --- 3. Add CORS Middleware ---
# This is CRITICAL to allow your Vercel frontend
# to talk to your Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Vercel, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- 4. Caching Logic (from main.py) ---
# Read DB_NAME from Environment Variables (set in Render dashboard)
DB_NAME = os.environ.get("DB_NAME", "analysis_cache.db")
CACHE_DURATION = 3600  # 1 hour

def init_db():
    # Make sure the directory for the db exists (for Render's disk)
    db_dir = os.path.dirname(DB_NAME)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cache
        (ticker TEXT PRIMARY KEY,
         analysis TEXT,
         timestamp REAL)
    ''')
    conn.commit()
    conn.close()

def get_cached_analysis(ticker):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT analysis, timestamp FROM cache WHERE ticker = ?", (ticker,))
        result = c.fetchone()
        conn.close()
        if result:
            analysis, timestamp = result
            if (time.time() - timestamp) < CACHE_DURATION:
                return analysis
    except sqlite3.OperationalError:
        # DB might not be initialized yet, or path is wrong
        print(f"Warning: Could not read from cache database at {DB_NAME}")
        return None
    return None

def set_cached_analysis(ticker, analysis):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("REPLACE INTO cache (ticker, analysis, timestamp) VALUES (?, ?, ?)",
                  (ticker, analysis, time.time()))
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print(f"Warning: Could not write to cache database at {DB_NAME}")

# --- 5. Main API Endpoint ---
@app.post("/api/analyze")
async def analyze_stock(request: AnalysisRequest):
    """
    This is the main API endpoint that the React frontend will call.
    It runs the complete analysis pipeline.
    """
    ticker = request.ticker.upper()
    print(f"--- Received new analysis request for {ticker} ---")
    
    # 1. Check cache
    cached_result = get_cached_analysis(ticker)
    if cached_result:
        print(f"Returning cached result for {ticker}.")
        return {"analysis": cached_result}

    print(f"--- Starting new analysis for {ticker} ---")
    
    try:
        # 2. Fetch Data
        print(f"Fetching fundamentals for {ticker}...")
        fundamentals, summary = get_fundamentals(ticker)
        if not fundamentals:
            return {"error": f"Could not fetch fundamental data for ticker: {ticker}"}

        print(f"Fetching news for {ticker}...")
        news = get_news(ticker, YOUR_API_KEY)
        
        # 3. Process & Embed (RAG)
        print("Processing and embedding data...")
        vector_index, text_chunks, metadata = process_and_embed(news, summary, ticker)
        
        # 4. Retrieve Relevant Chunks
        query = f"Recent news, developments, and user context for {ticker}"
        relevant_chunks, citations = retrieve_relevant_chunks(
            query, vector_index, text_chunks, metadata
        )
        
        # 5. Build Prompt & Get Analysis (Pass the user profile)
        print("Building prompt...")
        user_prompt = build_prompt(
            ticker=request.ticker,
            fundamentals=fundamentals,
            relevant_chunks=relevant_chunks,
            citations=citations,
            user_profile=request  
        )
        
        analysis = get_analysis(user_prompt)
        
        # 6. Add Citations to Analysis
        if citations:
            citation_header = "\n\n--- Sources ---\n"
            citation_list = "\n".join(citations)
            analysis += citation_header + citation_list
        
        # 7. Cache and return the result
        set_cached_analysis(ticker, analysis)
        print(f"--- Analysis for {ticker} complete. ---")
        return {"analysis": analysis}

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"An unexpected server error occurred: {e}"}

# --- 6. Run the Server ---
if __name__ == "__main__":
    print("--- Initializing database ---")
    init_db()
    
    print("--- Loading embedding model on startup ---")
    load_embedding_model() # Pre-load the model
    
    print("--- Starting FastAPI server ---")
    
    # Get port and host from environment for deployment
    port = int(os.environ.get("PORT", 8000))
    # Render's start command uses 0.0.0.0, so we default to that
    host = os.environ.get("HOST", "0.0.0.0") 
    
    print(f"--- Running on http://{host}:{port} ---")
    uvicorn.run(app, host=host, port=port)
