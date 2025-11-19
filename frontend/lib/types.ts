// --- Define the structure of the API request ---
export interface SearchFormState {
  ticker: string;
  financialCondition: string[];
  expectedReturn: number;
  riskTolerance: string;
  tradingPreferences: string;
}

// --- Define the structure of the API response ---
export interface ForecastData {
  month: string;
  price: number;
  type: 'history' | 'forecast';
}

export interface InvestmentAdviceData {
  entryPoint: number;
  expectedReturn: number;
  stopLoss: number;
}

export interface RecommendedStockData {
  ticker: string;
  name?: string;
  reason: string;
}

export interface AnalysisResult {
  forecastData: any[];
  investmentAdvice: any;
  recommendedStocks: any[];
  analysis: string;
  keyNews: string;
}
