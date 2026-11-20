import React from "react";

export default function StockDashboard() {
  return (
    <main className="p-8 max-w-5xl mx-auto font-sans">
      <h1 className="text-3xl font-bold mb-2">Stock Market Data Analyzer</h1>
      <p className="text-gray-600 mb-6">Interactive OHLCV charts, SMA20/SMA50 crossovers, and backtest metrics.</p>
      <div className="border rounded-lg p-4 bg-white shadow-sm">
        <p className="text-sm text-gray-500">Connect to FastAPI endpoints <code>GET /chart/AAPL</code> and <code>POST /backtest/sma</code>.</p>
      </div>
    </main>
  );
}
