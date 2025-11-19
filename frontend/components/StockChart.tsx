"use client";

import { BarChart, Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from "./components/ui/card"; // Using Shadcn/ui Card component

// --- FIX: Using relative path to import the type from page.tsx ---
import { ForecastData } from "./lib/types";

// Define the props for the chart component
interface StockChartProps {
  data: ForecastData[];
}

export function StockChart({ data }: StockChartProps) {
  
  // Handle cases where data might be null or undefined
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart className="h-6 w-6 mr-2 text-indigo-500" />
            12-Month Price Forecast
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-md">
            <Loader2 className="h-8 w-8 text-gray-500 animate-spin" />
            <p className="text-gray-500 ml-3">Waiting for data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Split data for styling
  const historyData = data.filter((d) => d.type === 'history');
  const forecastData = data.filter((d) => d.type === 'forecast');

  // Create a connector array to link the two lines seamlessly
  // It takes the last point of history and the first point of the forecast
  const connectorData: ForecastData[] = [];
  if (historyData.length > 0) {
    connectorData.push(historyData[historyData.length - 1]);
    if (forecastData.length > 0) {
      connectorData.push(forecastData[0]);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <BarChart className="h-6 w-6 mr-2 text-indigo-500" />
          12-Month Price Forecast
        </CardTitle>
        <CardDescription>
          AI-generated 12-month price trend based on fundamentals and news sentiment.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis 
                dataKey="month" 
                stroke="#9ca3af" // gray-400
                fontSize={12}
              />
              <YAxis 
                stroke="#9ca3af" 
                fontSize={12}
                domain={['auto', 'auto']}
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937", // gray-800
                  borderColor: "#374151", // gray-700
                  borderRadius: "0.5rem",
                  color: "#f9fafb" // gray-50
                }}
                labelStyle={{ color: "#f9fafb" }}
                itemStyle={{ color: "#f9fafb" }}
              />
              <Legend />
              
              {/* The solid "Historical" line */}
              <Line
                type="monotone"
                dataKey="price"
                data={historyData}
                stroke="#4f46e5" // indigo-600
                strokeWidth={2}
                name="Historical"
                dot={false}
              />
              
              {/* The dashed "Forecast" line */}
              <Line
                type="monotone"
                dataKey="price"
                data={forecastData}
                stroke="#a78bfa" // violet-400
                strokeWidth={2}
                name="Forecast"
                strokeDasharray="5 5"
                dot={false}
              />

              {/* A small, invisible line to bridge the gap */}
              <Line
                type="monotone"
                dataKey="price"
                data={connectorData}
                stroke="#4f46e5" // Use historical color to connect
                strokeWidth={2}
                dot={false}
                legendType="none" // Hide from legend
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
