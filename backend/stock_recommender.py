"""
Stock Recommendation System Module
Simplified version for production deployment
"""

import re
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

# Simplified import - remove relative import
from data_fetcher import get_fundamentals

# --- Stock Universe: Smaller set for production ---
POPULAR_STOCKS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA',
    # Healthcare
    'JNJ', 'PFE', 'UNH', 'ABT', 'MRK', 'LLY',
    # Consumer
    'WMT', 'HD', 'MCD', 'SBUX', 'NKE', 'COST',
    # Industrial
    'BA', 'CAT', 'HON',
    # Energy
    'XOM', 'CVX',
    # Communication
    'T', 'VZ', 'DIS'
]

# --- Sector Mapping ---
SECTOR_KEYWORDS = {
    'Technology': ['tech', 'software', 'hardware', 'cloud', 'ai', 'internet'],
    'Finance': ['bank', 'financial', 'investment', 'credit'],
    'Healthcare': ['health', 'medical', 'pharma', 'biotech'],
    'Consumer': ['retail', 'consumer', 'store', 'shopping'],
    'Energy': ['oil', 'gas', 'energy'],
    'Industrial': ['industrial', 'manufacturing'],
    'Communication': ['telecom', 'communication', 'media']
}

# --- Risk Level Mapping ---
RISK_LEVELS = {
    'Low': {'pe_range': (0, 20), 'volatility_preference': 'low', 'dividend_preference': 'high'},
    'Medium': {'pe_range': (10, 30), 'volatility_preference': 'medium', 'dividend_preference': 'medium'},
    'High': {'pe_range': (0, 50), 'volatility_preference': 'high', 'dividend_preference': 'low'}
}


def parse_trading_history(trading_history: str) -> Dict:
    """
    Parses natural language trading history to extract preferences.
    """
    if not trading_history or not isinstance(trading_history, str):
        return {'tickers': [], 'sectors': [], 'preferences': {}}
    
    text = trading_history.lower()
    parsed = {
        'tickers': [],
        'sectors': [],
        'preferences': {}
    }
    
    # Extract stock tickers
    ticker_pattern = r'\b[A-Z]{1,5}\b'
    potential_tickers = re.findall(ticker_pattern, trading_history.upper())
    for ticker in potential_tickers:
        if ticker in POPULAR_STOCKS:
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


def get_stock_universe(candidate_count: int = 50) -> List[str]:  # Reduced from 200 to 50
    """
    Gets a list of candidate stocks for recommendation.
    Uses a smaller, fixed list for production.
    """
    return POPULAR_STOCKS[:min(candidate_count, len(POPULAR_STOCKS))]


def fetch_stock_data(ticker: str) -> Optional[Dict]:
    """
    Fetches stock data with timeout handling.
    """
    try:
        fundamentals, summary = get_fundamentals(ticker)
        if not fundamentals:
            return None
        
        # Create simplified stock data
        stock_data = {
            'ticker': ticker,
            'fundamentals': fundamentals,
            'summary': summary,
            'sector': 'Unknown',  # Simplified for production
            'industry': 'Unknown',
            'volatility': 0.2,  # Default value
            'current_price': fundamentals.get('Current Price', 'N/A'),
            'market_cap': fundamentals.get('Market Cap', 'N/A'),
            'dividend_yield': fundamentals.get('Dividend Yield', 0),
            'pe_ratio': fundamentals.get('P/E Ratio (Trailing)', 'N/A'),
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
    Simplified scoring for production.
    """
    if not stock_data:
        return 0.0
    
    score = 0.5  # Base score
    
    # Simple sector matching
    if trading_history_parsed.get('sectors'):
        score += 0.2
    
    # Risk tolerance matching (simplified)
    risk_tolerance = user_profile.get('riskTolerance', 'Medium')
    if risk_tolerance == 'Low':
        score += 0.1
    elif risk_tolerance == 'High':
        score += 0.3
    
    return min(1.0, score)


def recommend_stocks(
    trading_history: str,
    financial_condition: List[str],
    expected_return: int,
    risk_tolerance: str,
    num_recommendations: int = 5  # Reduced from 10 to 5
) -> List[Dict]:
    """
    Simplified stock recommendation for production.
    """
    print("Starting simplified stock recommendation...")
    
    # Parse trading history
    trading_history_parsed = parse_trading_history(trading_history)
    print(f"Extracted: {len(trading_history_parsed['tickers'])} tickers, {len(trading_history_parsed['sectors'])} sectors")
    
    # Build user profile
    user_profile = {
        'financialCondition': financial_condition,
        'expectedReturn': expected_return,
        'riskTolerance': risk_tolerance,
        'tradingPreferences': trading_history
    }
    
    # Get candidate stocks (smaller set)
    candidate_stocks = get_stock_universe(candidate_count=30)
    print(f"Processing {len(candidate_stocks)} candidate stocks...")
    
    scored_stocks = []
    
    for i, ticker in enumerate(candidate_stocks):
        stock_data = fetch_stock_data(ticker)
        if not stock_data:
            continue
        
        score = calculate_stock_score(stock_data, user_profile, trading_history_parsed)
        
        # Simple reason generation
        reason = "Good match with your investment profile"
        if trading_history_parsed.get('sectors'):
            reason = f"Matches your interest in {trading_history_parsed['sectors'][0]} sector"
        
        scored_stocks.append({
            'ticker': ticker,
            'score': score,
            'sector': stock_data.get('sector', 'Unknown'),
            'reason': reason,
            'current_price': stock_data.get('current_price'),
            'pe_ratio': stock_data.get('pe_ratio'),
        })
    
    # Sort by score and return top N
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = scored_stocks[:num_recommendations]
    
    print(f"Recommendation complete. Selected {len(top_recommendations)} stocks.")
    
    return top_recommendations
