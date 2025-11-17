import React, { useState } from 'react';
import { create } from 'zustand';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart,
  User,
  Activity,
  Zap,
  Loader2,
  AlertTriangle,
  FileText,
  Briefcase,
  Target,
} from 'lucide-react';

// --- 1. DEFINE ZUSTAND STORE ---
// This is the "brain" of our application, holding all state.

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Mock data for initial UI display and development
const mockData = {
  analysis: "This is a mock analysis. Fill out the form and click 'Analyze' to get a live response.",
  keyNews: "Mock news summary. The backend will provide real data.",
  forecastData: [
    { month: 'Jan', price: 150, type: 'history' },
    { month: 'Feb', price: 155, type: 'history' },
    { month: 'Mar', price: 160, type: 'history' },
    { month: 'Apr', price: 165, type: 'history' },
    { month: 'May', price: 170, type: 'history' },
    { month: 'Jun', price: 175, type: 'history' },
    { month: 'Jul', price: 180, type: 'history' },
    { month: 'Aug', price: 185, type: 'history' },
    { month: 'Sep', price: 190, type: 'forecast' },
    { month: 'Oct', price: 195, type: 'forecast' },
    { month: 'Nov', price: 200, type: 'forecast' },
    { month: 'Dec', price: 205, type: 'forecast' },
  ],
  investmentAdvice: {
    entryPoint: 175.5,
    expectedReturn: 18.0,
    stopLoss: 168.0,
  },
  recommendedStocks: [
    {
      ticker: 'MSFT',
      name: 'Microsoft',
      reason: 'Matches your long-term, stable tech preference.',
    },
    {
      ticker: 'GOOGL',
      name: 'Google',
      reason: 'Aligns with your interest in high-growth tech.',
    },
  ],
};

const useAnalysisStore = create((set, get) => ({
  // 1. User Input State
  userInput: {
    ticker: 'AAPL',
    financialCondition: ['Stable Income'],
    expectedReturn: 15,
    riskTolerance: 'Medium',
    tradingPreferences: 'I am a long-term holder, I prefer tech and biotech.',
  },
  
  // 2. API / Data State
  isLoading: false,
  apiError: null,
  
  // 3. API Results
  analysisResults: mockData, // Start with mock data
  
  // 4. Actions (Functions to update state)
  
  // Helper to update any field in userInput
  setInput: (key, value) => {
    set((state) => ({
      userInput: { ...state.userInput, [key]: value },
    }));
  },
  
  // Main API call function
  fetchAnalysis: async () => {
    const { userInput } = get();
    set({ isLoading: true, apiError: null });

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, userInput);

      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      const aiResponseJsonString = response.data.analysis;
      if (!aiResponseJsonString || aiResponseJsonString.startsWith("Error:")) {
        throw new Error(aiResponseJsonString || "Empty response from AI");
      }

      const aiData = JSON.parse(aiResponseJsonString);

      // Success: Save the data
      set({
        analysisResults: aiData,
        isLoading: false,
      });
    } catch (error) {
      console.error("Error fetching analysis:", error);
      let errorMessage = "Failed to fetch analysis.";
      if (error.response) {
        errorMessage = `Server Error: ${error.response.data.detail || error.message}`;
      } else if (error.request) {
        errorMessage = `Connection Error: Is the Python server running at ${API_BASE_URL}?`;
      } else {
        errorMessage = error.message;
      }
      set({ isLoading: false, apiError: errorMessage });
    }
  },
}));

// --- 2. DEFINE SUB-COMPONENTS ---

function ProfileInputForm() {
  const { userInput, setInput, fetchAnalysis, isLoading } = useAnalysisStore();

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchAnalysis();
  };

  return (
    <div className="w-full md:w-1/3 lg:w-1/4 p-6 bg-gray-50 dark:bg-gray-900 overflow-y-auto h-screen sticky top-0">
      <h2 className="text-3xl font-bold mb-6 text-indigo-600 dark:text-indigo-400">
        AI Stock Analyzer
      </h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Stock Ticker */}
        <div>
          <label htmlFor="ticker" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Stock Ticker
          </label>
          <input
            type="text"
            id="ticker"
            value={userInput.ticker}
            onChange={(e) => setInput('ticker', e.target.value.toUpperCase())}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., AAPL"
            required
          />
        </div>

        {/* Risk Tolerance */}
        <div>
          <label htmlFor="riskTolerance" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Risk Tolerance
          </label>
          <select
            id="riskTolerance"
            value={userInput.riskTolerance}
            onChange={(e) => setInput('riskTolerance', e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
        </div>

        {/* Expected Return % */}
        <div>
          <label htmlFor="expectedReturn" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Expected Annual Return (%)
          </label>
          <input
            type="number"
            id="expectedReturn"
            value={userInput.expectedReturn}
            onChange={(e) => setInput('expectedReturn', parseInt(e.target.value, 10))}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., 15"
          />
        </div>

        {/* Financial Condition (Simplified as an example, you can expand this) */}
        <div>
          <label htmlFor="financialCondition" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Financial Condition
          </label>
          <input
            type="text"
            id="financialCondition"
            value={userInput.financialCondition.join(', ')} // Join array for display
            onChange={(e) => setInput('financialCondition', e.target.value.split(',').map(s => s.trim()))} // Split string into array
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., Stable Income, High Debt"
          />
        </div>

        {/* Trading History and Preferences */}
        <div>
          <label htmlFor="tradingPreferences" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Trading Preferences
          </label>
          <textarea
            id="tradingPreferences"
            rows="4"
            value={userInput.tradingPreferences}
            onChange={(e) => setInput('tradingPreferences', e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="e.g., I prefer long-term holds in the tech sector..."
          />
        </div>

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="animate-spin h-5 w-5" />
            ) : (
              <Zap className="h-5 w-5 mr-2" />
            )}
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </form>

      <div className="mt-8 text-xs text-gray-500 dark:text-gray-400">
        <p className="font-bold">Disclaimer:</p>
        <p>This is not financial advice. All analysis is generated by an AI and is for informational purposes only. Consult a professional before making any financial decisions.</p>
      </div>
    </div>
  );
}

function DashboardDisplay() {
  const { analysisResults, isLoading, apiError } = useAnalysisStore();

  if (isLoading) {
    return (
      <div className="flex-1 p-10 flex flex-col justify-center items-center h-screen bg-gray-100 dark:bg-gray-950">
        <Loader2 className="animate-spin h-16 w-16 text-indigo-600" />
        <h3 className="mt-4 text-xl font-semibold text-gray-700 dark:text-gray-300">Analyzing...</h3>
        <p className="text-gray-500 dark:text-gray-400">Please wait, the AI is processing your request.</p>
      </div>
    );
  }

  if (apiError) {
    return (
      <div className="flex-1 p-10 flex flex-col justify-center items-center h-screen bg-gray-100 dark:bg-gray-950">
        <AlertTriangle className="h-16 w-16 text-red-500" />
        <h3 className="mt-4 text-xl font-semibold text-red-600">An Error Occurred</h3>
        <p className="text-gray-500 dark:text-gray-400 text-center max-w-md">{apiError}</p>
      </div>
    );
  }

  // After loading, and no error, show the results.
  // We use a key on the main div to force a re-render when the ticker changes
  return (
    <div key={analysisResults.ticker} className="flex-1 p-10 overflow-y-auto h-screen bg-gray-100 dark:bg-gray-950">
      <h1 className="text-4xl font-bold mb-8 text-gray-900 dark:text-white">
        Analysis Dashboard
      </h1>
      
      {/* Main Grid for content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (Forecast & Advice) */}
        <div className="lg:col-span-2 space-y-8">
          <PriceForecast data={analysisResults.forecastData} />
          <InvestmentAdvice data={analysisResults.investmentAdvice} />
        </div>

        {/* Right Column (Recommendations & Summary) */}
        <div className="lg:col-span-1 space-y-8">
          <RecommendedStocks data={analysisResults.recommendedStocks} />
          <AnalysisSummary 
            analysis={analysisResults.analysis} 
            keyNews={analysisResults.keyNews} 
          />
        </div>
      </div>
    </div>
  );
}

function PriceForecast({ data }) {
  const historyData = data.filter(d => d.type === 'history');
  const forecastData = data.filter(d => d.type === 'forecast');
  
  // Add the last point of history to the forecast to connect the line
  const connector = historyData.length > 0 ? [historyData[historyData.length - 1], ...forecastData] : forecastData;

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
        <BarChart className="h-6 w-6 mr-2 text-indigo-500" />
        12-Month Price Forecast
      </h3>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#4B5563" />
            <XAxis dataKey="month" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'rgba(31, 41, 55, 0.8)', 
                borderColor: '#4B5563',
                borderRadius: '0.5rem',
              }}
              labelStyle={{ color: '#F9FAFB' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="price"
              data={historyData}
              stroke="#4F46E5"
              strokeWidth={2}
              name="Historical"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="price"
              data={connector}
              stroke="#4F46E5"
              strokeWidth={2}
              name="Forecast"
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function InvestmentAdvice({ data }) {
  const { entryPoint, expectedReturn, stopLoss } = data;
  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
        <Target className="h-6 w-6 mr-2 text-green-500" />
        AI Investment Advice
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard 
          title="Entry Point" 
          value={`$${entryPoint?.toFixed(2)}`}
          icon={<DollarSign className="text-blue-500" />} 
        />
        <StatCard 
          title="Expected Return" 
          value={`${expectedReturn?.toFixed(1)}%`}
          icon={<TrendingUp className="text-green-500" />} 
        />
        <StatCard 
          title="Stop Loss" 
          value={`$${stopLoss?.toFixed(2)}`}
          icon={<TrendingDown className="text-red-500" />} 
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }) {
  return (
    <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg flex items-center">
      <div className="p-3 rounded-full bg-gray-200 dark:bg-gray-700 mr-4">
        {React.cloneElement(icon, { className: 'h-6 w-6' })}
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}

function RecommendedStocks({ data = [] }) {
  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
        <Briefcase className="h-6 w-6 mr-2 text-purple-500" />
        Recommended Stocks
      </h3>
      <ul className="space-y-4">
        {data.map((stock) => (
          <li key={stock.ticker} className="border-b border-gray-200 dark:border-gray-800 pb-3 last:border-b-0">
            <div className="flex justify-between items-center">
              <span className="font-bold text-lg text-gray-900 dark:text-white">{stock.ticker}</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">{stock.name}</span>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{stock.reason}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function AnalysisSummary({ analysis, keyNews }) {
  return (
    <>
      <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
          <FileText className="h-6 w-6 mr-2 text-yellow-500" />
          AI Analysis
        </h3>
        <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{analysis}</p>
      </div>
      <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
          <Activity className="h-6 w-6 mr-2 text-cyan-500" />
          Key News
        </h3>
        <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{keyNews}</p>
      </div>
    </>
  );
}


// --- 3. DEFINE THE MAIN APP ---
// This component ties everything together.

export default function App() {
  // We can add a simple dark mode toggle here for fun
  const [isDarkMode, setIsDarkMode] = useState(true);

  return (
    <div className={isDarkMode ? 'dark' : ''}>
      <div className="flex flex-col md:flex-row min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-white">
        <button
          onClick={() => setIsDarkMode(!isDarkMode)}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-gray-200 dark:bg-gray-800"
          aria-label="Toggle dark mode"
        >
          {isDarkMode ? '☀️' : '🌙'}
        </button>
        
        {/* Left Side: The Form */}
        <ProfileInputForm />
        
        {/* Right Side: The Dashboard */}
        <DashboardDisplay />
      </div>
    </div>
  );
}
