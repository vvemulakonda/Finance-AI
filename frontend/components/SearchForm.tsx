"use client";

import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import { Loader2, Zap } from "lucide-react";

// --- 1. Define the props this component will receive ---
export interface SearchFormState {
  ticker: string;
  financialCondition: string[];
  expectedReturn: number;
  riskTolerance: string;
  tradingPreferences: string;
}

interface SearchFormProps {
  formState: SearchFormState;
  setFormState: (
    update: (prevState: SearchFormState) => SearchFormState
  ) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

// --- 2. Create the "controlled" component ---
// It no longer has its own state. It gets everything from its parent (page.tsx).
export function SearchForm({
  formState,
  setFormState,
  handleSubmit,
  isLoading,
}: SearchFormProps) {
  
  // Helper function to update a single field
  const handleChange = (
    key: keyof SearchFormState,
    value: string | number | string[]
  ) => {
    // This calls the updater function in the parent
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Stock Ticker */}
      <div>
        <Label htmlFor="ticker">Stock Ticker</Label>
        <Input
          id="ticker"
          value={formState.ticker}
          onChange={(e) => handleChange("ticker", e.target.value.toUpperCase())}
          placeholder="e.g., AAPL"
          required
        />
      </div>

      {/* Risk Tolerance */}
      <div>
        <Label htmlFor="riskTolerance">Risk Tolerance</Label>
        <Select
          value={formState.riskTolerance}
          onValueChange={(value) => handleChange("riskTolerance", value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select risk level" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Low">Low</SelectItem>
            <SelectItem value="Medium">Medium</SelectItem>
            <SelectItem value="High">High</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Expected Return % */}
      <div>
        <Label htmlFor="expectedReturn">Expected Annual Return (%)</Label>
        <Input
          id="expectedReturn"
          type="number"
          value={formState.expectedReturn}
          onChange={(e) => handleChange("expectedReturn", parseInt(e.target.value, 10) || 0)}
          placeholder="e.g., 15"
        />
      </div>

      {/* Financial Condition */}
      <div>
        <Label htmlFor="financialCondition">Financial Condition</Label>
        <Input
          id="financialCondition"
          value={formState.financialCondition.join(", ")}
          onChange={(e) =>
            handleChange("financialCondition", e.target.value.split(",").map((s) => s.trim())) // <-- FIX: Corrected typo
          }
          placeholder="e.g., Stable Income, High Debt"
        />
      </div>

      {/* Trading History and Preferences */}
      <div>
        <Label htmlFor="tradingPreferences">Trading Preferences</Label>
        <Textarea
          id="tradingPreferences"
          rows={4}
          value={formState.tradingPreferences}
          onChange={(e) => handleChange("tradingPreferences", e.target.value)}
          placeholder="e.g., I prefer long-term holds in the tech sector..."
        />
      </div>

      {/* Submit Button */}
      <div>
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <Loader2 className="animate-spin h-5 w-5" />
          ) : (
            <Zap className="h-5 w-5 mr-2" />
          )}
          {isLoading ? "Analyzing..." : "Analyze"}
        </Button>
      </div>
    </form>
  );
}
