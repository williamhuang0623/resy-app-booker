import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import SettingsPage from "./pages/SettingsPage";
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

function ProtectedLayout() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#555",
          fontSize: 14,
        }}
      >
        Loading…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "0 20px" }}>
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

        <nav style={{ display: "flex", gap: 28, alignItems: "center" }}>
          <NavLink to="/" end style={({ isActive }) => (isActive ? activeStyle : navStyle)}>
            Dates
          </NavLink>
          <NavLink to="/hitlist" style={({ isActive }) => (isActive ? activeStyle : navStyle)}>
            Hitlist
          </NavLink>
          <NavLink to="/settings" style={({ isActive }) => (isActive ? activeStyle : navStyle)}>
            Settings
          </NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<DatesPage />} />
          <Route path="/hitlist" element={<HitlistPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPageGuard />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  );
}

function LoginPageGuard() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  if (user) return <Navigate to="/" replace />;
  return <LoginPage />;
}
