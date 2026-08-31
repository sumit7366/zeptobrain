import { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
const fmtCr = (n) => n >= 10000000 ? `₹${(n/10000000).toFixed(2)}Cr` : n >= 100000 ? `₹${(n/100000).toFixed(1)}L` : `₹${fmt(n)}`;

function Badge({ level }) {
  const colors = {
    critical: "bg-red-100 text-red-700 border border-red-300",
    high: "bg-orange-100 text-orange-700 border border-orange-300",
    medium: "bg-yellow-100 text-yellow-700 border border-yellow-300",
    safe: "bg-green-100 text-green-700 border border-green-300",
    HIGH: "bg-red-100 text-red-700 border border-red-300",
    MEDIUM: "bg-orange-100 text-orange-700 border border-orange-300",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${colors[level] || "bg-gray-100 text-gray-600"}`}>
      {level}
    </span>
  );
}

function StatCard({ title, value, sub, color = "blue", icon }) {
  const colors = {
    blue: "from-blue-500 to-blue-600",
    red: "from-red-500 to-red-600",
    green: "from-green-500 to-green-600",
    orange: "from-orange-500 to-orange-600",
    purple: "from-purple-500 to-purple-600",
  };
  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl p-4 text-white shadow-lg`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm opacity-80">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
        </div>
        <span className="text-3xl opacity-80">{icon}</span>
      </div>
    </div>
  );
}

// ── Tab: Overview ─────────────────────────────────────────────────────────────
function Overview({ summary, roi, stores }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Weekly Waste" value={fmtCr(summary?.week_waste_inr || 0)}
          sub={`${summary?.waste_pct_of_revenue?.toFixed(1)}% of revenue`} color="red" icon="🗑️" />
        <StatCard title="Spoilage Alerts" value={summary?.spoilage_alerts?.critical || 0}
          sub={`${summary?.spoilage_alerts?.total || 0} total alerts`} color="orange" icon="⚠️" />
        <StatCard title="Transfer Recs" value={summary?.transfer_recommendations || 0}
          sub={`Save ${fmtCr(summary?.transfer_potential_savings_inr || 0)}`} color="purple" icon="🔄" />
        <StatCard title="Annual Savings" value={fmtCr(roi?.annual_savings_inr || 0)}
          sub={`${roi?.reduction_pct}% waste reduction`} color="green" icon="💰" />
      </div>

      {/* Stores grid */}
      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-3">🏪 Dark Stores</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stores.map(s => (
            <div key={s.store_id} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-gray-800">{s.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{s.store_id} • {s.locality}</p>
                </div>
                <span className="text-2xl">📍</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div className="bg-green-50 rounded-lg p-2">
                  <p className="text-xs text-gray-500">Revenue (Annual)</p>
                  <p className="font-bold text-green-700">{fmtCr(s.total_revenue_inr)}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-2">
                  <p className="text-xs text-gray-500">Waste (Annual)</p>
                  <p className="font-bold text-red-600">{fmtCr(s.total_waste_inr)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ROI Panel */}
      {roi && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-5">
          <h2 className="text-lg font-bold text-green-800 mb-3">💡 ZeptoBrain ROI Impact</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">Before ZeptoBrain</p>
              <p className="text-xl font-bold text-red-600">{fmtCr(roi.annual_waste_before_inr)}</p>
              <p className="text-xs text-gray-400">annual waste</p>
            </div>
            <div className="flex items-center justify-center text-3xl">→</div>
            <div>
              <p className="text-xs text-gray-500">After ZeptoBrain</p>
              <p className="text-xl font-bold text-green-600">{fmtCr(roi.annual_waste_after_inr)}</p>
              <p className="text-xs text-gray-400">annual waste</p>
            </div>
          </div>
          <div className="mt-4 text-center">
            <p className="text-2xl font-bold text-green-700">💰 {fmtCr(roi.annual_savings_inr)} saved annually</p>
            <p className="text-sm text-gray-500 mt-1">{roi.skus_tracked} SKUs tracked across {roi.stores} stores • {roi.data_points.toLocaleString()} data points</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Tab: Spoilage Alerts ──────────────────────────────────────────────────────
function SpoilageAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/spoilage-alerts?top_n=50`)
      .then(r => r.json())
      .then(d => { setAlerts(d.alerts || []); setLoading(false); });
  }, []);

  const filtered = filter === "all" ? alerts : alerts.filter(a => a.risk_level === filter);
  const totalLoss = filtered.reduce((s, a) => s + a.potential_loss_inr, 0);

  const pieData = [
    { name: "Critical", value: alerts.filter(a => a.risk_level === "critical").length, color: "#ef4444" },
    { name: "High", value: alerts.filter(a => a.risk_level === "high").length, color: "#f97316" },
    { name: "Medium", value: alerts.filter(a => a.risk_level === "medium").length, color: "#eab308" },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <h2 className="text-lg font-bold text-gray-800">⚠️ Spoilage Alerts</h2>
        <div className="flex gap-2">
          {["all","critical","high","medium"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-colors ${
                filter === f ? "bg-orange-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? <div className="p-8 text-center text-gray-400">Loading alerts...</div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left p-3 font-semibold text-gray-600">Product</th>
                    <th className="text-left p-3 font-semibold text-gray-600">Store</th>
                    <th className="text-center p-3 font-semibold text-gray-600">Score</th>
                    <th className="text-center p-3 font-semibold text-gray-600">Risk</th>
                    <th className="text-right p-3 font-semibold text-gray-600">Expires</th>
                    <th className="text-right p-3 font-semibold text-gray-600">Loss</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((a, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="p-3">
                        <p className="font-medium text-gray-800">{a.product_name}</p>
                        <p className="text-xs text-gray-400">{a.category}</p>
                      </td>
                      <td className="p-3 text-gray-600">{a.store_name}</td>
                      <td className="p-3 text-center">
                        <div className="inline-flex items-center justify-center w-10 h-10 rounded-full font-bold text-sm"
                          style={{ background: `hsl(${120 - a.spoilage_score * 1.2}, 70%, 90%)`,
                                   color: `hsl(${120 - a.spoilage_score * 1.2}, 70%, 35%)` }}>
                          {a.spoilage_score}
                        </div>
                      </td>
                      <td className="p-3 text-center"><Badge level={a.risk_level} /></td>
                      <td className="p-3 text-right text-gray-600">
                        {a.days_to_expire === 0 ? <span className="text-red-600 font-bold">EXPIRED</span>
                          : `${a.days_to_expire}d`}
                      </td>
                      <td className="p-3 text-right font-semibold text-red-600">
                        ₹{fmt(a.potential_loss_inr)}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={6} className="p-8 text-center text-gray-400">No alerts for this filter</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <p className="text-sm text-gray-500 mb-2">Alert Distribution</p>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={65}
                  dataKey="value" label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                  {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-sm text-gray-500">Total Potential Loss</p>
            <p className="text-2xl font-bold text-red-600 mt-1">₹{fmt(totalLoss)}</p>
            <p className="text-xs text-gray-400 mt-1">across {filtered.length} items</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Forecast ─────────────────────────────────────────────────────────────
function Forecast({ skus, stores }) {
  const [selectedStore, setSelectedStore] = useState("MUM001");
  const [selectedSku, setSelectedSku] = useState("");
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);

  const storeSkus = skus.filter(s => !selectedStore || true); // show all for simplicity

  useEffect(() => {
    if (storeSkus.length > 0 && !selectedSku) {
      setSelectedSku(storeSkus[0]?.sku_id || "");
    }
  }, [storeSkus, selectedSku]);

  const loadForecast = () => {
    if (!selectedStore || !selectedSku) return;
    setLoading(true);
    fetch(`${API}/forecast?store_id=${selectedStore}&sku_id=${selectedSku}&days=7`)
      .then(r => r.json())
      .then(d => { setForecast(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  const chartData = forecast ? [
    ...forecast.historical.slice(-7).map(h => ({
      date: h.date.slice(5), actual: h.units_sold, ordered: h.stock_ordered, type: "historical"
    })),
    ...forecast.forecast.map(f => ({
      date: f.date.slice(5), predicted: f.predicted_units,
      weekend: f.is_weekend ? f.predicted_units : null, type: "forecast"
    }))
  ] : [];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-800">🔮 Demand Forecast (XGBoost)</h2>

      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3 mb-4">
          <select value={selectedStore} onChange={e => setSelectedStore(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white">
            {stores.map(s => <option key={s.store_id} value={s.store_id}>{s.name}</option>)}
          </select>
          <select value={selectedSku} onChange={e => setSelectedSku(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white flex-1 min-w-48">
            {storeSkus.map(s => <option key={s.sku_id} value={s.sku_id}>{s.product_name}</option>)}
          </select>
          <button onClick={loadForecast} disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            {loading ? "Loading..." : "Get Forecast"}
          </button>
        </div>

        {forecast && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-lg text-sm font-medium">
                📦 {forecast.product_name}
              </span>
              <span className="bg-gray-50 text-gray-600 px-3 py-1 rounded-lg text-sm">
                MRP ₹{forecast.mrp}
              </span>
              {forecast.is_perishable && (
                <span className="bg-orange-50 text-orange-600 px-3 py-1 rounded-lg text-sm">
                  ⚡ Perishable • {forecast.shelf_life_days}d shelf life
                </span>
              )}
              <span className="bg-green-50 text-green-700 px-3 py-1 rounded-lg text-sm font-medium">
                📋 Recommended Order: {forecast.recommended_order} units
              </span>
            </div>

            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line dataKey="actual" stroke="#3b82f6" strokeWidth={2} dot name="Actual Sold"
                  connectNulls={false} />
                <Line dataKey="ordered" stroke="#94a3b8" strokeWidth={1} strokeDasharray="4 4"
                  dot={false} name="Stock Ordered" connectNulls={false} />
                <Line dataKey="predicted" stroke="#f97316" strokeWidth={2.5} dot={{ r: 5 }}
                  name="AI Forecast" strokeDasharray="6 2" connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-7 gap-1">
              {forecast.forecast.map((f, i) => (
                <div key={i} className={`rounded-lg p-2 text-center text-xs ${
                  f.is_weekend ? "bg-orange-50 border border-orange-200" : "bg-blue-50 border border-blue-100"}`}>
                  <p className="font-medium text-gray-600">{f.day.slice(0,3)}</p>
                  <p className="font-bold text-lg text-gray-800">{f.predicted_units}</p>
                  <p className="text-gray-400">units</p>
                  {f.is_weekend && <p className="text-orange-500 font-medium">📈WKD</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {!forecast && !loading && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-3">📊</p>
            <p>Select a store and product, then click Get Forecast</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tab: Transfers ────────────────────────────────────────────────────────────
function Transfers() {
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/transfers`)
      .then(r => r.json())
      .then(d => { setRecs(d.recommendations || []); setLoading(false); });
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold text-gray-800">🔄 Inter-Store Transfer Optimizer</h2>
        {recs.length > 0 && (
          <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-semibold">
            💰 Save ₹{fmt(recs.reduce((s,r) => s+r.total_impact_inr, 0))}
          </span>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-700">
        <strong>How it works:</strong> When Store A has excess stock of a perishable item AND Store B is running low on the same item, 
        ZeptoBrain suggests a transfer — preventing wastage at A and stockout at B simultaneously.
      </div>

      {loading ? <div className="text-center py-8 text-gray-400">Analyzing inventory across stores...</div> : (
        recs.length === 0 ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center text-green-600">
            <p className="text-3xl mb-2">✅</p>
            <p className="font-semibold">Inventory is balanced across all stores</p>
            <p className="text-sm text-gray-500 mt-1">No transfers needed right now</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recs.map((r, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex flex-wrap justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <p className="text-xs text-gray-400">FROM</p>
                      <p className="font-semibold text-gray-700">{r.from_store}</p>
                    </div>
                    <div className="flex flex-col items-center">
                      <p className="text-orange-500 font-bold text-lg">→</p>
                      <p className="text-xs text-gray-400">{r.distance_km} km</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-400">TO</p>
                      <p className="font-semibold text-gray-700">{r.to_store}</p>
                    </div>
                  </div>
                  <Badge level={r.urgency} />
                </div>

                <div className="mt-3 flex flex-wrap gap-2 items-center">
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium">
                    📦 {r.product_name}
                  </span>
                  <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-lg text-sm">
                    Transfer: {r.transfer_qty} units
                  </span>
                  {r.is_perishable && (
                    <span className="bg-orange-50 text-orange-600 px-3 py-1 rounded-lg text-sm">
                      ⚡ {r.shelf_life_days}d shelf life
                    </span>
                  )}
                </div>

                <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
                  <div className="bg-red-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-400">Wastage Saved</p>
                    <p className="font-bold text-red-600">₹{fmt(r.wastage_saved_inr)}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-400">Revenue Saved</p>
                    <p className="font-bold text-green-600">₹{fmt(r.revenue_saved_inr)}</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-400">Total Impact</p>
                    <p className="font-bold text-purple-600">₹{fmt(r.total_impact_inr)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}

// ── Tab: Waste Trend ──────────────────────────────────────────────────────────
function WasteTrend() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch(`${API}/waste-trend`)
      .then(r => r.json())
      .then(d => setData(d.filter((_, i) => i % 3 === 0))); // sample every 3 days
  }, []);

  const monthly = data.reduce((acc, d) => {
    const month = d.date.slice(0, 7);
    if (!acc[month]) acc[month] = { month, waste: 0, revenue: 0 };
    acc[month].waste += d.waste_inr;
    acc[month].revenue += d.revenue;
    return acc;
  }, {});
  const monthlyArr = Object.values(monthly);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold text-gray-800">📈 Waste & Revenue Trends</h2>

      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p className="text-sm font-semibold text-gray-600 mb-3">Monthly Waste vs Revenue (₹)</p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={monthlyArr}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `₹${(v/1000).toFixed(0)}K`} />
            <Tooltip formatter={v => `₹${fmt(v)}`} />
            <Legend />
            <Bar dataKey="revenue" name="Revenue" fill="#22c55e" radius={[4,4,0,0]} />
            <Bar dataKey="waste" name="Waste" fill="#ef4444" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p className="text-sm font-semibold text-gray-600 mb-3">Daily Waste Trend (₹)</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={14} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `₹${(v/1000).toFixed(0)}K`} />
            <Tooltip formatter={v => `₹${fmt(v)}`} />
            <Line dataKey="waste_inr" name="Daily Waste" stroke="#ef4444" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("overview");
  const [summary, setSummary] = useState(null);
  const [roi, setRoi] = useState(null);
  const [stores, setStores] = useState([]);
  const [skus, setSkus] = useState([]);
  const [connected, setConnected] = useState(null);

  useEffect(() => {
    // Check API connection
    fetch(`${API.replace('/api','')}`)
      .then(r => { if(r.ok) setConnected(true); else setConnected(false); })
      .catch(() => setConnected(false));

    fetch(`${API}/summary`).then(r => r.json()).then(setSummary).catch(() => {});
    fetch(`${API}/roi`).then(r => r.json()).then(setRoi).catch(() => {});
    fetch(`${API}/stores`).then(r => r.json()).then(setStores).catch(() => {});
    fetch(`${API}/skus`).then(r => r.json()).then(setSkus).catch(() => {});
  }, []);

  const tabs = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "forecast", label: "Forecast", icon: "🔮" },
    { id: "spoilage", label: "Spoilage", icon: "⚠️" },
    { id: "transfers", label: "Transfers", icon: "🔄" },
    { id: "trends", label: "Trends", icon: "📈" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">🧠 ZeptoBrain</h1>
              <p className="text-slate-400 text-sm">Dark Store Inventory Intelligence</p>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                connected === true ? "bg-green-500/20 text-green-400" :
                connected === false ? "bg-red-500/20 text-red-400" : "bg-gray-500/20 text-gray-400"}`}>
                <span className={`w-2 h-2 rounded-full ${
                  connected === true ? "bg-green-400 animate-pulse" :
                  connected === false ? "bg-red-400" : "bg-gray-400"}`} />
                {connected === true ? "API Live" : connected === false ? "API Offline" : "Connecting..."}
              </span>
              {summary?.data_as_of && (
                <span className="text-slate-400 text-xs">Data: {summary.data_as_of}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  tab === t.id
                    ? "border-orange-500 text-orange-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"}`}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {tab === "overview" && <Overview summary={summary} roi={roi} stores={stores} />}
        {tab === "forecast" && <Forecast skus={skus} stores={stores} />}
        {tab === "spoilage" && <SpoilageAlerts />}
        {tab === "transfers" && <Transfers />}
        {tab === "trends" && <WasteTrend />}
      </div>
    </div>
  );
}
