import uvicorn
import sqlite3
import time
import sys
import os
import json # --- NEW IMPORT ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager # For startup/shutdown events

# --- Import from our other files ---
try:
    # Import all necessary functions from your helper files
    from data_fetcher import (
        get_fundamentals, 
        get_news, 
        process_and_embed, 
        load_embedding_model, 
        download_nltk_data  
    )
    from ai_logic import retrieve_relevant_chunks, build_prompt, get_analysis
    # --- NEW IMPORT for the recommender ---
    from stock_recommender import recommend_stocks

except ImportError as e:
    print(f"Error: Could not import from helper files: {e}")
    print("Please make sure all .py files are in the same directory.")
    sys.exit(1)

# --- !! IMPORTANT !! ---
# Load API keys from Environment Variables (set in Render dashboard)
YOUR_API_KEY = os.environ.get("YOUR_API_KEY")
if not YOUR_API_KEY:
    print("Error: YOUR_API_KEY (for NewsAPI) is not set as an environment variable.")

# --- 1. Define API Models ---
class AnalysisRequest(BaseModel):
    ticker: str
    financialCondition: List[str]
    expectedReturn: int
    riskTolerance: str
    tradingPreferences: str

# --- 2. FastAPI Lifespan Event ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function runs on server startup and shutdown.
    """
    print("--- Server starting up... ---")
    print("--- Initializing database ---")
    init_db()
    print("--- Downloading NLTK data (if needed) ---")
    download_nltk_data()
    print("--- Pre-loading embedding model ---")
    load_embedding_model() # Pre-load the model
    print("--- Startup complete. Server is ready. ---")
    
    yield  # The application runs here
    
    print("--- Server shutting down... ---")

# --- 3. Initialize FastAPI App ---
app = FastAPI(lifespan=lifespan) 

# --- 4. Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- 5. Caching Logic ---
DB_NAME = os.environ.get("DB_NAME", "analysis_cache.db")
CACHE_DURATION = 3600  # 1 hour

def init_db():
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
        print(f"Warning: Could not read from cache database at {DB_NAME}")
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

# --- 6. Main API Endpoint (UPDATED) ---
@app.post("/api/analyze")
async def analyze_stock(request: AnalysisRequest):
    """
    This is the main API endpoint that the React frontend will call.
    It now orchestrates *both* the AI analysis and the rule-based recommender.
    """
    if not YOUR_API_KEY:
        return {"error": "Server Configuration Error: NewsAPI key is not set."}

    ticker = request.ticker.upper()
    print(f"--- Received new analysis request for {ticker} ---")
    
    # 1. Check cache
    cached_result = get_cached_analysis(ticker)
    if cached_result:
        print(f"Returning cached result for {ticker}.")
        return {"analysis": cached_result}

    print(f"--- Starting new analysis for {ticker} ---")
    
    try:
        # --- TASK 1: Get AI Analysis (Forecast, Advice) ---
        print(f"Fetching fundamentals for {ticker}...")
        fundamentals, summary = get_fundamentals(ticker)
        if not fundamentals:
            return {"error": f"Could not fetch fundamental data for ticker: {ticker}"}

        print(f"Fetching news for {ticker}...")
        news = get_news(ticker, YOUR_API_KEY)
        
        print("Processing and embedding data...")
        vector_index, text_chunks, metadata = process_and_embed(news, summary, ticker)
        
        query = f"Recent news, developments, and user context for {ticker}"
        relevant_chunks, citations = retrieve_relevant_chunks(
            query, vector_index, text_chunks, metadata
        )
        
        print("Building AI prompt...")
        user_prompt = build_prompt(
            ticker=request.ticker,
            fundamentals=fundamentals,
            relevant_chunks=relevant_chunks,
            citations=citations,
            user_profile=request  
        )
        
        # This is a JSON string: '{"analysis": "...", "forecastData": [...]...}'
        ai_json_string = get_analysis(user_prompt)
        
        # --- TASK 2: Get Rule-Based Recommendations ---
        print("Running rule-based stock recommender...")
        recommendations_list = recommend_stocks(
            trading_history=request.tradingPreferences,
            financial_condition=request.financialCondition,
            expected_return=request.expectedReturn,
            risk_tolerance=request.riskTolerance
        )
        
        # --- TASK 3: Combine Results ---
        print("Combining AI analysis and recommendations...")
        
        # Parse the AI's JSON string into a Python dict
        ai_data = json.loads(ai_json_string)
        
        # Add the new recommendations list to this dict
        ai_data['recommendedStocks'] = recommendations_list
        
        # Add citations if they exist
        if citations:
            citation_header = "\n\n--- Sources ---\n"
            citation_list = "\n".join(citations)
            ai_data['analysis'] += citation_header + citation_list # Add to the analysis text
        
        # Convert the *final, combined* dict back into a JSON string
        final_json_string = json.dumps(ai_data)
        
        # 7. Cache and return the final result
        set_cached_analysis(ticker, final_json_string)
        print(f"--- Analysis for {ticker} complete. ---")
        return {"analysis": final_json_string} # Send the final string

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"An unexpected server error occurred: {e}"}

# --- 7. Run the Server ---
if __name__ == "__main__":
    print("--- Starting FastAPI server ---")
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0") 
    print(f"--- Running on http://{host}:{port} ---")
    uvicorn.run("api_server:app", host=host, port=port, reload=False)
