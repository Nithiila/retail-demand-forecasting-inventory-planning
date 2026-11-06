import { useState } from "react";
import Dashboard from "./Dashboard.jsx";
import Forecast from "./Forecast.jsx";
import Inventory from "./Inventory.jsx";
import "./app.css";

export default function App() {
  const [view, setView] = useState("overview");
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">R</span><span>RetailOps</span></div><nav aria-label="Main navigation">
      {[['overview', 'Overview'], ['forecast', 'Forecasts'], ['inventory', 'Inventory'], ['risk', 'Risk & actions']].map(([id, label]) => <button key={id} className={view === id ? "nav-item active" : "nav-item"} onClick={() => setView(id)}>{label}</button>)}
    </nav><div className="sidebar-foot">Demand planning<br /><span>Weekly workspace</span></div></aside>
    <main className="main-content"><header className="topbar"><div><p className="eyebrow">OPERATIONS CONTROL</p><h1>Retail demand command center</h1></div><div className="status-pill"><span /> API connected</div></header>
      {view === "overview" && <Dashboard onNavigate={setView} />}{view === "forecast" && <Forecast />}{view === "inventory" && <Inventory />}{view === "risk" && <Inventory focus="risk" />}
    </main>
  </div>;
}
