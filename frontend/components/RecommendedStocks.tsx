"use client";
import { Briefcase } from "lucide-react";
// --- FIX: Using relative path to import the type from page.tsx ---
import { InvestmentAdvice } from "../components/InvestmentAdvice.tsx";

// This is a placeholder.
export function RecommendedStocks({ data }: { data: RecommendedStockData[] }) {
  
  // Handle cases where data might be null or undefined initially
  const safeData = data || []; // Ensure data is an array

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
        <Briefcase className="h-6 w-6 mr-2 text-purple-500" />
        Recommended Stocks
      </h3>
      <ul className="space-y-4">
        {safeData.length > 0 ? (
          safeData.map((stock) => (
            <li key={stock.ticker} className="border-b border-gray-200 dark:border-gray-800 pb-3 last:border-b-0">
              <div className="flex justify-between items-center">
                <span className="font-bold text-lg text-gray-900 dark:text-white">{stock.ticker}</span>
                {/* Use optional chaining in case name is not provided */}
                <span className="text-sm text-gray-600 dark:text-gray-400">{stock?.name}</span>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{stock.reason}</p>
            </li>
          ))
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">No recommendations available.</p>
        )}
      </ul>
    </div>
  );
}
