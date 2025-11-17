"""
Stock Recommendation System Module

This module provides functionality to recommend stocks based on:
- User's trading history (parsed from natural language)
- Financial condition
- Expected returns
- Risk tolerance

It uses yfinance for data fetching (imported from data_fetcher) and
scikit-learn/pandas for scoring and ranking stocks.
"""

import re
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from data_fetcher import get_fundamentals

# --- Stock Universe: Popular stocks for recommendation ---
# Using a mix of S&P 500 major stocks across different sectors
POPULAR_STOCKS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'V', 'MA',
    # Healthcare
    'JNJ', 'PFE', 'UNH', 'ABT', 'TMO', 'ABBV', 'MRK', 'LLY', 'AMGN',
    # Consumer
    'WMT', 'HD', 'MCD', 'SBUX', 'NKE', 'TGT', 'COST',
    # Industrial
    'BA', 'CAT', 'GE', 'HON', 'MMM', 'DE',
    # Energy
    'XOM', 'CVX', 'COP', 'SLB',
    # Communication
    'T', 'VZ', 'CMCSA', 'DIS',
    # Utilities
    'NEE', 'DUK', 'SO',
    # Real Estate
    'AMT', 'PLD', 'EQIX',
    # Materials
    'LIN', 'APD', 'SHW',
    # Consumer Staples
    'PG', 'KO', 'PEP', 'CL', 'CLX'
]

# --- Sector Mapping for stock classification ---
SECTOR_KEYWORDS = {
    'Technology': ['tech', 'software', 'hardware', 'cloud', 'ai', 'artificial intelligence', 
                   'semiconductor', 'chip', 'internet', 'social media', 'app', 'platform'],
    'Finance': ['bank', 'financial', 'investment', 'credit', 'loan', 'mortgage', 'insurance'],
    'Healthcare': ['health', 'medical', 'pharma', 'pharmaceutical', 'biotech', 'hospital', 
                   'drug', 'medicine', 'treatment'],
    'Consumer': ['retail', 'consumer', 'store', 'shopping', 'restaurant', 'food', 'beverage'],
    'Energy': ['oil', 'gas', 'energy', 'petroleum', 'renewable', 'solar', 'wind', 'power'],
    'Industrial': ['industrial', 'manufacturing', 'machinery', 'construction', 'aerospace'],
    'Communication': ['telecom', 'communication', 'media', 'entertainment', 'broadcast'],
    'Utilities': ['utility', 'electric', 'water', 'gas utility'],
    'Real Estate': ['real estate', 'property', 'reit', 'realty'],
    'Materials': ['chemical', 'material', 'mining', 'steel', 'metal'],
    'Consumer Staples': ['consumer goods', 'household', 'personal care', 'grocery']
}

# --- Risk Level Mapping ---
RISK_LEVELS = {
    'Low': {'pe_range': (0, 20), 'volatility_preference': 'low', 'dividend_preference': 'high'},
    'Medium': {'pe_range': (10, 30), 'volatility_preference': 'medium', 'dividend_preference': 'medium'},
    'High': {'pe_range': (0, 50), 'volatility_preference': 'high', 'dividend_preference': 'low'}
}


def parse_trading_history(trading_history: str) -> Dict:
    """
    Parses natural language trading history to extract:
    - Stock tickers mentioned
    - Sectors of interest
    - Trading patterns (buy/sell frequency, holding periods)
    - Stock types (growth, value, dividend)
    
    Args:
        trading_history: Natural language string describing trading history
        
    Returns:
        Dictionary with parsed information:
        {
            'tickers': List[str],
            'sectors': List[str],
            'preferences': Dict
        }
    """
    if not trading_history or not isinstance(trading_history, str):
        return {'tickers': [], 'sectors': [], 'preferences': {}}
    
    text = trading_history.lower()
    parsed = {
        'tickers': [],
        'sectors': [],
        'preferences': {}
    }
    
    # Extract stock tickers (uppercase 1-5 letter codes)
    ticker_pattern = r'\b[A-Z]{1,5}\b'
    potential_tickers = re.findall(ticker_pattern, trading_history.upper())
    # Filter to known tickers or common patterns
    for ticker in potential_tickers:
        if ticker in POPULAR_STOCKS or len(ticker) >= 2:
            if ticker not in parsed['tickers']:
                parsed['tickers'].append(ticker)
    
    # Identify sectors mentioned
    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                if sector not in parsed['sectors']:
                    parsed['sectors'].append(sector)
                break
    
    # Identify preferences
    if any(word in text for word in ['growth', 'growing', 'growth stock']):
        parsed['preferences']['type'] = 'growth'
    elif any(word in text for word in ['value', 'undervalued', 'cheap']):
        parsed['preferences']['type'] = 'value'
    elif any(word in text for word in ['dividend', 'income', 'yield']):
        parsed['preferences']['type'] = 'dividend'
    
    if any(word in text for word in ['long term', 'long-term', 'hold', 'holding']):
        parsed['preferences']['holding_period'] = 'long'
    elif any(word in text for word in ['short term', 'short-term', 'trade', 'trading']):
        parsed['preferences']['holding_period'] = 'short'
    
    return parsed


def get_stock_universe(candidate_count: int = 500) -> List[str]:
    """
    Gets a list of candidate stocks for recommendation.
    Tries to fetch S&P 500 list dynamically, falls back to POPULAR_STOCKS if fetch fails.
    
    Args:
        candidate_count: Maximum number of stocks to consider (default 500 for S&P 500)
        
    Returns:
        List of stock tickers
    """
    # Try to fetch S&P 500 list from Wikipedia
    try:
        print("Fetching S&P 500 stock list...")
        # Fetch S&P 500 list from Wikipedia
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_table = tables[0]  # First table contains the S&P 500 companies
        tickers = sp500_table['Symbol'].tolist()
        
        # Clean up tickers (remove dots that indicate share classes, e.g., "BRK.B" -> "BRK-B")
        cleaned_tickers = [ticker.replace('.', '-') for ticker in tickers]
        
        print(f"Successfully fetched {len(cleaned_tickers)} S&P 500 stocks")
        # Return limited by candidate_count
        return cleaned_tickers[:candidate_count]
        
    except Exception as e:
        print(f"Could not fetch S&P 500 list: {e}")
        print("Falling back to POPULAR_STOCKS list...")
        # Fallback to the hardcoded popular stocks list
        return POPULAR_STOCKS[:min(candidate_count, len(POPULAR_STOCKS))]


def fetch_stock_data(ticker: str) -> Optional[Dict]:
    """
    Fetches comprehensive stock data using yfinance.
    Uses get_fundamentals from data_fetcher to maintain consistency.
    
    NOTE: yfinance can fetch data for ANY valid ticker symbol worldwide,
    not just stocks in POPULAR_STOCKS or S&P 500. The stock universe list
    is only used to limit the candidate pool for recommendations.
    
    Args:
        ticker: Stock ticker symbol (can be any valid ticker, e.g., 'AAPL', 'TSLA', '7203.T' for Japanese stocks, etc.)
        
    Returns:
        Dictionary with stock data, or None if fetch fails
    """
    try:
        # Use existing get_fundamentals function
        fundamentals, summary = get_fundamentals(ticker)
        if not fundamentals:
            return None
        
        # Get additional data from yfinance for scoring
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # Get historical data for volatility calculation
        hist = ticker_obj.history(period="1y")
        if hist.empty:
            volatility = None
        else:
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Get sector and industry
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        
        # Compile all data
        stock_data = {
            'ticker': ticker,
            'fundamentals': fundamentals,
            'summary': summary,
            'sector': sector,
            'industry': industry,
            'volatility': volatility,
            'current_price': info.get('currentPrice', None),
            'market_cap': info.get('marketCap', None),
            'dividend_yield': info.get('dividendYield', 0) if info.get('dividendYield') else 0,
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'peg_ratio': info.get('pegRatio', None),
            'roe': info.get('returnOnEquity', None),
            'debt_to_equity': info.get('debtToEquity', None),
            '52_week_high': info.get('fiftyTwoWeekHigh', None),
            '52_week_low': info.get('fiftyTwoWeekLow', None),
        }
        
        return stock_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def calculate_stock_score(
    stock_data: Dict,
    user_profile: Dict,
    trading_history_parsed: Dict
) -> float:
    """
    Calculates a recommendation score for a stock based on user profile.
    Uses multiple factors weighted appropriately.
    
    Args:
        stock_data: Dictionary with stock information
        user_profile: User's financial condition, expected returns, risk tolerance
        trading_history_parsed: Parsed trading history information
        
    Returns:
        Float score (higher is better)
    """
    if not stock_data:
        return 0.0
    
    score = 0.0
    weights = {
        'sector_match': 0.25,
        'risk_match': 0.25,
        'return_match': 0.20,
        'financial_health': 0.15,
        'preference_match': 0.15
    }
    
    # 1. Sector Match Score (0-1)
    sector_score = 0.0
    stock_sector = stock_data.get('sector', 'Unknown')
    if trading_history_parsed.get('sectors'):
        if stock_sector in trading_history_parsed['sectors']:
            sector_score = 1.0
        else:
            # Partial match based on industry keywords
            sector_score = 0.3
    else:
        # No sector preference, neutral score
        sector_score = 0.5
    
    score += weights['sector_match'] * sector_score
    
    # 2. Risk Match Score (0-1)
    risk_tolerance = user_profile.get('riskTolerance', 'Medium')
    risk_config = RISK_LEVELS.get(risk_tolerance, RISK_LEVELS['Medium'])
    
    risk_score = 0.5  # Default neutral
    
    pe_ratio = stock_data.get('pe_ratio')
    volatility = stock_data.get('volatility')
    dividend_yield = stock_data.get('dividend_yield', 0)
    
    if pe_ratio and pe_ratio != 'N/A':
        try:
            pe_val = float(pe_ratio) if isinstance(pe_ratio, (int, float)) else 0
            pe_min, pe_max = risk_config['pe_range']
            if pe_min <= pe_val <= pe_max:
                risk_score += 0.3
        except (ValueError, TypeError):
            pass
    
    if volatility:
        vol_pref = risk_config['volatility_preference']
        if vol_pref == 'low' and volatility < 0.25:
            risk_score += 0.2
        elif vol_pref == 'medium' and 0.15 <= volatility <= 0.35:
            risk_score += 0.2
        elif vol_pref == 'high' and volatility > 0.25:
            risk_score += 0.2
    
    if dividend_yield:
        div_pref = risk_config['dividend_preference']
        div_yield_val = float(dividend_yield) if isinstance(dividend_yield, (int, float)) else 0
        if div_pref == 'high' and div_yield_val > 0.02:
            risk_score += 0.2
        elif div_pref == 'medium' and 0.01 <= div_yield_val <= 0.03:
            risk_score += 0.2
        elif div_pref == 'low' and div_yield_val < 0.02:
            risk_score += 0.2
    
    risk_score = min(1.0, risk_score)  # Cap at 1.0
    score += weights['risk_match'] * risk_score
    
    # 3. Expected Return Match Score (0-1)
    expected_return = user_profile.get('expectedReturn', 10)
    return_score = 0.5  # Default neutral
    
    # Estimate potential return based on fundamentals
    roe = stock_data.get('roe')
    peg = stock_data.get('peg_ratio')
    
    if roe and roe != 'N/A':
        try:
            roe_val = float(roe) if isinstance(roe, (int, float)) else 0
            # Higher ROE suggests better returns
            if roe_val > expected_return / 10:  # Convert percentage expectation
                return_score += 0.3
        except (ValueError, TypeError):
            pass
    
    if peg and peg != 'N/A':
        try:
            peg_val = float(peg) if isinstance(peg, (int, float)) else 0
            # PEG < 1 suggests undervalued/good growth potential
            if 0 < peg_val < 1.5:
                return_score += 0.2
        except (ValueError, TypeError):
            pass
    
    return_score = min(1.0, return_score)
    score += weights['return_match'] * return_score
    
    # 4. Financial Health Score (0-1)
    health_score = 0.5  # Default neutral
    
    roe = stock_data.get('roe')
    debt_to_equity = stock_data.get('debt_to_equity')
    
    if roe and roe != 'N/A':
        try:
            roe_val = float(roe) if isinstance(roe, (int, float)) else 0
            if roe_val > 0.15:  # Good ROE
                health_score += 0.25
            elif roe_val > 0.10:
                health_score += 0.15
        except (ValueError, TypeError):
            pass
    
    if debt_to_equity and debt_to_equity != 'N/A':
        try:
            de_val = float(debt_to_equity) if isinstance(debt_to_equity, (int, float)) else 0
            if 0 < de_val < 1.0:  # Reasonable debt
                health_score += 0.25
        except (ValueError, TypeError):
            pass
    
    health_score = min(1.0, health_score)
    score += weights['financial_health'] * health_score
    
    # 5. Preference Match Score (0-1)
    pref_score = 0.5  # Default neutral
    
    preferences = trading_history_parsed.get('preferences', {})
    pref_type = preferences.get('type')
    
    if pref_type == 'growth':
        # Look for growth indicators (high PEG, high ROE, low dividend)
        if peg and peg != 'N/A':
            try:
                peg_val = float(peg) if isinstance(peg, (int, float)) else 0
                if 0 < peg_val < 2.0:
                    pref_score += 0.3
            except (ValueError, TypeError):
                pass
        if dividend_yield and float(dividend_yield) < 0.01:
            pref_score += 0.2
    
    elif pref_type == 'value':
        # Look for value indicators (low P/E, low P/B)
        if pe_ratio and pe_ratio != 'N/A':
            try:
                pe_val = float(pe_ratio) if isinstance(pe_ratio, (int, float)) else 0
                if 0 < pe_val < 20:
                    pref_score += 0.3
            except (ValueError, TypeError):
                pass
    
    elif pref_type == 'dividend':
        # Look for dividend yield
        if dividend_yield and float(dividend_yield) > 0.02:
            pref_score += 0.5
    
    pref_score = min(1.0, pref_score)
    score += weights['preference_match'] * pref_score
    
    return score


def recommend_stocks(
    trading_history: str,
    financial_condition: List[str],
    expected_return: int,
    risk_tolerance: str,
    num_recommendations: int = 10
) -> List[Dict]:
    """
    Main function to recommend stocks based on user profile.
    
    Args:
        trading_history: Natural language trading history
        financial_condition: List of financial condition descriptors
        expected_return: Expected return percentage (e.g., 10 for 10%)
        risk_tolerance: 'Low', 'Medium', or 'High'
        num_recommendations: Number of stocks to recommend (default 10)
        
    Returns:
        List of dictionaries, each containing:
        {
            'ticker': str,
            'score': float,
            'sector': str,
            'reason': str,
            'fundamentals': Dict
        }
    """
    print(f"--- Starting stock recommendation process ---")
    
    # 1. Parse trading history
    print("Parsing trading history...")
    trading_history_parsed = parse_trading_history(trading_history)
    print(f"Ext
