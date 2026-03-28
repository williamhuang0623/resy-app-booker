import { useState } from "react";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function SettingsPage() {
  const { user, logout, login } = useAuth();

  const [resyEmail, setResyEmail] = useState("");
  const [resyPassword, setResyPassword] = useState("");
  const [resyApiKey, setResyApiKey] = useState("VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    setSaving(true);
    try {
      await authApi.updateCredentials(resyEmail.trim(), resyPassword, resyApiKey.trim());
      // Refresh user state so the "credentials saved" indicator updates
      const token = localStorage.getItem("token")!;
      await login(token);
      setSaved(true);
      setResyPassword("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save credentials");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>
          Settings
        </h1>
        <p style={{ color: "#777", fontSize: 14 }}>
          Manage your account and Resy credentials.
        </p>
      </div>

      {/* Account info */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Account</h2>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 14, color: "#ccc" }}>{user?.email}</div>
            <div style={{ fontSize: 12, color: "#555", marginTop: 4 }}>
              Resy credentials: {user?.has_resy_credentials
                ? <span style={{ color: "#4caf7a" }}>saved</span>
                : <span style={{ color: "#f0a04a" }}>not set</span>}
            </div>
          </div>
          <button onClick={logout} style={ghostBtnStyle}>
            Sign out
          </button>
        </div>
      </section>

      {/* Resy credentials */}
      <section style={{ ...sectionStyle, marginTop: 20 }}>
        <h2 style={sectionTitleStyle}>Resy Credentials</h2>
        <p style={{ color: "#666", fontSize: 13, marginBottom: 20 }}>
          Your credentials are encrypted before being stored and only decrypted
          at booking time. They are never exposed via the API.
        </p>

        <form onSubmit={handleSave}>
          <label style={labelStyle}>Resy email</label>
          <input
            type="email"
            value={resyEmail}
            onChange={(e) => setResyEmail(e.target.value)}
            placeholder="your-resy-account@email.com"
            required
            style={inputStyle}
          />

          <label style={{ ...labelStyle, marginTop: 16 }}>Resy password</label>
          <input
            type="password"
            value={resyPassword}
            onChange={(e) => setResyPassword(e.target.value)}
            placeholder="your Resy password"
            required
            style={inputStyle}
          />

          <label style={{ ...labelStyle, marginTop: 16 }}>
            Resy API key
            <span style={{ color: "#555", fontWeight: 400, marginLeft: 6, textTransform: "none" }}>
              (leave default if unsure)
            </span>
          </label>
          <input
            type="text"
            value={resyApiKey}
            onChange={(e) => setResyApiKey(e.target.value)}
            placeholder="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"
            required
            style={inputStyle}
          />

          {error && (
            <div style={errorStyle}>{error}</div>
          )}

          {saved && (
            <div
              style={{
                background: "#0a2a1a",
                border: "1px solid #1a5a3a",
                borderRadius: 8,
                color: "#4caf7a",
                fontSize: 13,
                marginTop: 16,
                padding: "10px 14px",
              }}
            >
              Credentials saved successfully.
            </div>
          )}

          <button
            type="submit"
            disabled={saving}
            style={{
              background: saving ? "#333" : "#ff6b4a",
              border: "none",
              borderRadius: 10,
              color: "#fff",
              cursor: saving ? "not-allowed" : "pointer",
              fontSize: 14,
              fontWeight: 700,
              marginTop: 24,
              padding: "12px 28px",
              transition: "background 0.15s",
            }}
          >
            {saving ? "Saving…" : "Save credentials"}
          </button>
        </form>
      </section>
    </div>
  );
}

const sectionStyle: React.CSSProperties = {
  background: "#111",
  border: "1px solid #1e1e1e",
  borderRadius: 14,
  padding: "24px 28px",
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 700,
  marginBottom: 16,
  letterSpacing: "-0.01em",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  color: "#888",
  fontSize: 12,
  fontWeight: 600,
  letterSpacing: "0.06em",
  marginBottom: 6,
  textTransform: "uppercase",
};

const inputStyle: React.CSSProperties = {
  background: "#0a0a0a",
  border: "1px solid #2a2a2a",
  borderRadius: 8,
  color: "#fff",
  fontSize: 14,
  outline: "none",
  padding: "11px 14px",
  width: "100%",
  boxSizing: "border-box",
};

const ghostBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "1px solid #2a2a2a",
  borderRadius: 8,
  color: "#888",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  padding: "7px 16px",
};

const errorStyle: React.CSSProperties = {
  background: "#2a0a0a",
  border: "1px solid #5a1a1a",
  borderRadius: 8,
  color: "#ff6b6b",
  fontSize: 13,
  marginTop: 16,
  padding: "10px 14px",
};
