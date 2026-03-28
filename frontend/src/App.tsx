import { NavLink, Route, Routes } from "react-router-dom";
import DatesPage from "./pages/DatesPage";
import HitlistPage from "./pages/HitlistPage";

const navStyle: React.CSSProperties = {
  textDecoration: "none",
  color: "#888",
  fontWeight: 600,
  fontSize: 14,
  letterSpacing: "0.05em",
  textTransform: "uppercase",
  padding: "6px 0",
  borderBottom: "2px solid transparent",
  transition: "color 0.15s, border-color 0.15s",
};

const activeStyle: React.CSSProperties = {
  ...navStyle,
  color: "#ff6b4a",
  borderBottomColor: "#ff6b4a",
};

export default function App() {
  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "0 20px" }}>
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "24px 0 20px",
          borderBottom: "1px solid #222",
          marginBottom: 32,
        }}
      >
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.03em" }}>
            Resy Booker
          </div>
          <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>
            auto-book hard-to-get tables
          </div>
        </div>

        <nav style={{ display: "flex", gap: 28 }}>
          <NavLink
            to="/"
            end
            style={({ isActive }) => (isActive ? activeStyle : navStyle)}
          >
            Dates
          </NavLink>
          <NavLink
            to="/hitlist"
            style={({ isActive }) => (isActive ? activeStyle : navStyle)}
          >
            Hitlist
          </NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<DatesPage />} />
          <Route path="/hitlist" element={<HitlistPage />} />
        </Routes>
      </main>
    </div>
  );
}
