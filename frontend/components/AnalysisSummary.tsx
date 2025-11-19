'use client';

import { FileText, Newspaper } from "lucide-react";

// Define the props interface
interface AnalysisSummaryProps {
  analysis: string;
  keyNews: string;
}

// --- 1. Define the props this component will receive ---
export function AnalysisSummary({ analysis, keyNews }: AnalysisSummaryProps) {
  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-lg space-y-6">
      {/* Analysis Section */}
      <div>
        <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
          <FileText className="h-6 w-6 mr-2 text-blue-500" />
          AI Analysis
        </h3>
        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {analysis || "No analysis available."}
          </p>
        </div>
      </div>

      {/* Key News Section */}
      <div>
        <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
          <Newspaper className="h-6 w-6 mr-2 text-orange-500" />
          Key News
        </h3>
        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {keyNews || "No news available."}
          </p>
        </div>
      </div>
    </div>
  );
}
