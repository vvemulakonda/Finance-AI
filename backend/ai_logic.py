import sys
import os

# --- Import AI/LLM libraries ---
try:
    import google.generativeai as genai
except ImportError:
    print("Error: The 'google-generativeai' library is not installed.")
    print("Please install it using: pip install google-generativeai")
    sys.exit(1)

# --- !! IMPORTANT !! ---
# Load API key from environment variable (set in Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Configure the Gemini API ---
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        print("Error: GEMINI_API_KEY is not set in ai_logic.py or environment.")
        sys.exit(1)
        
    model = genai.GenerativeModel('gemini-1.0-pro') # Using the stable 'gemini-1.0-pro'
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure your API key is correct and valid.")
    sys.exit(1)

# --- 1. RAG Retrieval ---

def retrieve_relevant_chunks(query, vector_index, text_chunks, metadata, k=5):
    """
    Searches the FAISS index for the top-k most relevant text chunks.
    """
    if vector_index is None:
        print("Vector index is not available.")
        return [], []
    
    # 1. Embed the query
    try:
        from data_fetcher import embedding_model
        if embedding_model is None:
            print("Error: Embedding model not loaded from data_fetcher.")
            return [], []
        query_embedding = embedding_model.encode([query])
    except Exception as e:
        print(f"Error encoding query: {e}")
        return [], []

    # 2. Search the FAISS index
    try:
        D, I = vector_index.search(query_embedding, k)
    except Exception as e:
        print(f"Error searching FAISS index: {e}")
        return [], []

    # 3. Format the results
    relevant_chunks = []
    citations = set()  # Use a set to avoid duplicate citations
    
    for i, chunk_index in enumerate(I[0]):
        if chunk_index < 0 or chunk_index >= len(text_chunks):
            continue
            
        chunk = text_chunks[chunk_index]
        meta = metadata[chunk_index]
        
        # --- Use .get() to provide default values ---
        source_name = meta.get('source', 'Unknown Source')
        source_url = meta.get('url', '#')
        source_date = meta.get('date', 'N/A')
        
        citation_str = f"[{source_name}]({source_url}) - {source_date}"
        
        relevant_chunks.append(f"Source: {citation_str}\nContent: {chunk}")
        citations.add(citation_str)

    return relevant_chunks, list(citations)

# --- 2. Prompt Engineering (UPDATED) ---

def build_prompt(ticker, fundamentals, relevant_chunks, citations, user_profile):
    """
    Builds the final prompt string to send to the LLM.
    This is now UPDATED to only ask for analysis and forecast.
    """
    
    # --- System Prompt: The AI's "Instructions" ---
    system_prompt = """
You are an expert financial analyst and portfolio manager. Your task is to provide a comprehensive, data-driven analysis for a *specific user* based on their profile and the provided data.

**USER PROFILE:**
- **Financial Condition:** {user_profile.financialCondition}
- **Risk Tolerance:** {user_profile.riskTolerance}
- **Expected Return %:** {user_profile.expectedReturn}%
- **Trading Preferences:** {user_profile.tradingPreferences}

**YOUR TASK:**
Analyze the provided stock data and generate a personalized report. The user is asking for:
1.  A 12-month price forecast.
2.  Specific investment advice (entry point, return %, stop loss).

**RULES:**
1.  Do NOT use any external knowledge. Base your *entire* analysis on the provided data.
2.  **CRITICAL:** You *must* generate the 12-month forecast and investment advice, even if the data is limited. Use the fundamentals and news sentiment to make logical estimations.
3.  The user's profile is the most important context. All advice *must* be tailored to their risk tolerance.
4.  The output must be formatted *exactly* as a single JSON object. Do not include markdown formatting (```json) or any text outside the curly braces.

**REQUIRED JSON OUTPUT FORMAT:**
{{
  "analysis": "...",
  "keyNews": "...",
  "forecastData": [
    {{"month": "Jan", "price": 150, "type": "history"}},
    {{"month": "Feb", "price": 155, "type": "history"}},
    {{"month": "Mar", "price": 160, "type": "history"}},
    {{"month": "Apr", "price": 165, "type": "history"}},
    {{"month": "May", "price": 170, "type": "history"}},
    {{"month": "Jun", "price": 175, "type": "history"}},
    {{"month": "Jul", "price": 180, "type": "history"}},
    {{"month": "Aug", "price": 185, "type": "history"}},
    {{"month": "Sep", "price": 190, "type": "forecast"}},
    {{"month": "Oct", "price": 195, "type": "forecast"}},
    {{"month": "Nov", "price": 200, "type": "forecast"}},
    {{"month": "Dec", "price": 205, "type": "forecast"}}
  ],
  "investmentAdvice": {{
    "entryPoint": 175.50,
    "expectedReturn": 18.0,
    "stopLoss": 168.00
  }}
}}
"""
    
    # --- User Prompt: The "Data" ---
    
    # Format the fundamentals data
    fundamentals_str = "\n".join(f"- {key}: {value}" for key, value in fundamentals.items())
    
    # Format the news chunks
    if relevant_chunks:
        news_str = "\n\n---\n\n".join(relevant_chunks)
    else:
        news_str = "No recent news articles were found or provided."
        
    # Combine it all
    # We use .format() on the system prompt to insert the user's profile
    formatted_system_prompt = system_prompt.format(user_profile=user_profile)
    
    user_prompt_data = f"""
--- START OF DATA ---

**Stock Ticker:**
{ticker}

**Financial Indicators:**
{fundamentals_str}

**Recent News Articles:**
{news_str}

--- END OF DATA ---

Please provide your analysis based *only* on the data above, following all rules and the required JSON format.
"""
    
    return formatted_system_prompt + user_prompt_data

# --- 3. AI Generation (UPDATED) ---

def get_analysis(prompt_text):
    """
    Sends the prompt to the Gemini API and gets the response.
    UPDATED to tell Gemini to return JSON.
    """
    if not GEMINI_API_KEY:
        return "Error: Gemini API key is not configured."
        
    try:
        print("Generating analysis with Gemini API...")
        
        # --- NEW: Tell the model to output JSON ---
        generation_config = {
            "response_mime_type": "application/json",
        }
        
        response = model.generate_content(
            prompt_text,
            generation_config=generation_config
        )
        # The response.text will now be a JSON string
        return response.text
        
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return f"Error: Could not get analysis from API. Details: {e}"
